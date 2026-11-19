"""Tests de sécurité : authentification, autorisations, injections, exposition de données."""
import base64
import json
from datetime import datetime, timedelta, timezone

import jwt
import pytest
from sqlalchemy import func, select, text

from app import config
from app.models import Booking, User
from tests.helpers import book, login, register, room_id_by_name, slot

PROTECTED_ROUTES = [
    ("GET", "/api/auth/me"),
    ("GET", "/api/rooms"),
    ("GET", "/api/rooms/amenities"),
    ("GET", "/api/rooms/1"),
    ("GET", "/api/rooms/1/availability?date=2030-01-01"),
    ("GET", "/api/bookings"),
    ("POST", "/api/bookings"),
    ("DELETE", "/api/bookings/1"),
]


def _b64(data: dict) -> str:
    return base64.urlsafe_b64encode(json.dumps(data).encode()).decode().rstrip("=")


def _call(client, method: str, path: str, headers: dict | None = None):
    return client.request(method, path, headers=headers or {}, json={} if method == "POST" else None)


# ----------------------------------------------------------- Mots de passe & données sensibles
def test_st01_password_is_stored_hashed(client, db_session):
    """Inscription avec le mot de passe « Passw0rd! ».
    Attendu : en base, password_hash est un hash bcrypt et ne contient pas le mot de passe."""
    register(client, "alice", "alice@example.com", "Passw0rd!")
    user = db_session.scalar(select(User).where(User.email == "alice@example.com"))
    assert user.password_hash.startswith("$2")
    assert "Passw0rd!" not in user.password_hash


def test_st02_no_secret_is_ever_returned(client):
    """Réponses d'inscription, de connexion et de /me.
    Attendu : aucune ne contient de champ ou de valeur « password » / hash bcrypt."""
    created = register(client, "alice", "alice@example.com")
    logged = login(client, "alice@example.com")
    token = logged.json()["access_token"]
    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    for response in (created, logged, me):
        assert "password" not in response.text.lower()
        assert "$2b$" not in response.text


def test_st03_jwt_payload_has_no_personal_data(client):
    """Contenu (non signé) du jeton d'accès.
    Attendu : uniquement sub, iat et exp (pas d'e-mail, de mot de passe ou de rôle)."""
    register(client, "alice", "alice@example.com")
    token = login(client, "alice@example.com").json()["access_token"]
    claims = jwt.decode(token, options={"verify_signature": False})
    assert set(claims) == {"sub", "iat", "exp"}


# ------------------------------------------------------------------------ Authentification / JWT
@pytest.mark.parametrize("method,path", PROTECTED_ROUTES)
def test_st04_protected_routes_require_a_token(client, method, path):
    """Appel de chaque route protégée sans jeton.
    Attendu : 401 sur toutes les routes."""
    assert _call(client, method, path).status_code == 401


@pytest.mark.parametrize(
    "authorization",
    ["Bearer n.importe.quoi", "Bearer ", "Bearer", "Basic YWxpY2U6cGFzcw==", "bearer-sans-espace", "Bearer a.b.c.d"],
)
def test_st05_malformed_credentials_are_refused(client, authorization):
    """En-tête Authorization mal formé ou jeton invalide.
    Attendu : 401."""
    assert client.get("/api/auth/me", headers={"Authorization": authorization}).status_code == 401


def test_st06_expired_token_is_refused(client, alice):
    """Jeton authentique mais expiré depuis 1 minute.
    Attendu : 401."""
    from app.security import create_access_token

    expired = create_access_token(alice.id, expires_delta=timedelta(minutes=-1))
    assert client.get("/api/auth/me", headers={"Authorization": f"Bearer {expired}"}).status_code == 401


def test_st07_token_signed_with_wrong_key_is_refused(client, alice):
    """Jeton forgé avec une autre clé secrète mais avec l'identifiant d'Alice.
    Attendu : 401."""
    exp = datetime.now(timezone.utc) + timedelta(hours=1)
    forged = jwt.encode({"sub": str(alice.id), "exp": exp}, "cle-d-attaquant-0123456789abcdefghij", algorithm="HS256")
    assert client.get("/api/auth/me", headers={"Authorization": f"Bearer {forged}"}).status_code == 401


def test_st08_unsigned_alg_none_token_is_refused(client, alice):
    """Jeton « alg: none » (sans signature) prétendant être Alice.
    Attendu : 401 (seul HS256 est accepté)."""
    exp = int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp())
    forged = f"{_b64({'alg': 'none', 'typ': 'JWT'})}.{_b64({'sub': str(alice.id), 'exp': exp})}."
    assert client.get("/api/auth/me", headers={"Authorization": f"Bearer {forged}"}).status_code == 401


def test_st09_token_of_unknown_user_is_refused(client):
    """Jeton correctement signé mais pour un utilisateur qui n'existe pas (ou plus).
    Attendu : 401."""
    from app.security import create_access_token

    ghost = create_access_token(987654)
    assert client.get("/api/auth/me", headers={"Authorization": f"Bearer {ghost}"}).status_code == 401


def test_st10_tampered_token_payload_is_refused(client, alice, bob):
    """Alice modifie l'identifiant (sub) de son jeton pour devenir Bob, sans re-signer.
    Attendu : 401."""
    header, payload, signature = alice.token.split(".")
    claims = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
    claims["sub"] = str(bob.id)
    forged = f"{header}.{_b64(claims)}.{signature}"
    assert client.get("/api/auth/me", headers={"Authorization": f"Bearer {forged}"}).status_code == 401


def test_st11_login_does_not_reveal_whether_email_exists(client):
    """Connexion avec un e-mail existant (mauvais mot de passe) puis avec un e-mail inconnu.
    Attendu : même code (401) et même message : impossible de deviner les comptes existants."""
    register(client, "alice", "alice@example.com")
    known = login(client, "alice@example.com", "MauvaisMdp1")
    unknown = login(client, "personne@example.com", "MauvaisMdp1")
    assert known.status_code == unknown.status_code == 401
    assert known.json() == unknown.json()


# ------------------------------------------------------------------------------------ Injections
@pytest.mark.parametrize("payload", ["' OR '1'='1", "admin'--", "'; DROP TABLE users; --", "\" OR \"\"=\""])
def test_st12_sql_injection_in_login_fails_and_data_is_intact(client, db_session, payload):
    """Connexion avec une injection SQL en guise d'e-mail et de mot de passe.
    Attendu : 401 (jamais 200 ni 500) et la table users est intacte."""
    register(client, "alice", "alice@example.com")
    response = client.post("/api/auth/login", json={"email": payload, "password": payload})
    assert response.status_code == 401
    assert db_session.scalar(select(func.count(User.id))) == 1


def test_st13_sql_injection_in_registration_is_rejected(client, db_session):
    """Inscription avec une injection SQL dans le nom d'utilisateur et dans l'e-mail.
    Attendu : 422, aucun compte créé et les tables existent toujours."""
    response = client.post(
        "/api/auth/register",
        json={
            "username": "x'; DROP TABLE users; --",
            "email": "a'; DROP TABLE users; --@example.com",
            "password": "Passw0rd!",
        },
    )
    assert response.status_code == 422
    assert db_session.scalar(select(func.count(User.id))) == 0


def test_st14_sql_injection_in_room_filters_is_harmless(client, alice, db_session):
    """Filtres de chambres avec des injections SQL (équipement, capacité, date).
    Attendu : aucun 500, aucune fuite de données (liste vide ou 422) et les tables sont intactes."""
    injected_amenity = client.get("/api/rooms", params={"amenity": "' OR 1=1; --"}, headers=alice.headers)
    assert injected_amenity.status_code == 200 and injected_amenity.json() == []
    injected_capacity = client.get("/api/rooms", params={"min_capacity": "1 OR 1=1"}, headers=alice.headers)
    assert injected_capacity.status_code == 422
    injected_date = client.get("/api/rooms/1/availability", params={"date": "2030-01-01' OR '1'='1"}, headers=alice.headers)
    assert injected_date.status_code == 422
    assert db_session.execute(text("SELECT count(*) FROM rooms")).scalar() == 8


@pytest.mark.parametrize("username", ["<script>alert(1)</script>", "<img src=x onerror=alert(1)>", "\"><svg/onload=alert(1)>"])
def test_st15_xss_payload_in_username_is_rejected(client, db_session, username):
    """Inscription avec un nom d'utilisateur contenant du JavaScript / HTML.
    Attendu : 422 et rien n'est enregistré (pas de XSS stocké)."""
    response = register(client, username, "xss@example.com")
    assert response.status_code == 422
    assert db_session.scalar(select(func.count(User.id))) == 0


# ------------------------------------------------------------------------ Autorisations (IDOR)
def test_st16_user_cannot_cancel_another_users_booking(client, alice, bob):
    """Bob tente d'annuler la réservation d'Alice (accès direct par identifiant).
    Attendu : 404 et la réservation d'Alice reste confirmée."""
    room = room_id_by_name(client, alice.headers, "Salle Monet")
    booking_id = book(client, alice, room, *slot()).json()["id"]
    assert client.delete(f"/api/bookings/{booking_id}", headers=bob.headers).status_code == 404
    assert client.get("/api/bookings", headers=alice.headers).json()[0]["status"] == "confirmed"


def test_st17_user_cannot_see_another_users_bookings(client, alice, bob):
    """Bob consulte « mes réservations » alors qu'Alice en a une.
    Attendu : liste vide pour Bob ; la disponibilité d'une chambre n'expose pas l'identité d'Alice."""
    room = room_id_by_name(client, alice.headers, "Salle Monet")
    start, end = slot()
    book(client, alice, room, start, end)
    assert client.get("/api/bookings", headers=bob.headers).json() == []
    availability = client.get(f"/api/rooms/{room}/availability", params={"date": start[:10]}, headers=bob.headers)
    assert "alice" not in availability.text.lower()


def test_st18_extra_fields_cannot_escalate_or_impersonate(client, alice, bob, db_session):
    """Mass assignment : inscription avec is_admin/id imposés, réservation avec le user_id de Bob.
    Attendu : champs ignorés ; la réservation appartient à Alice (utilisateur du jeton), pas à Bob."""
    created = client.post(
        "/api/auth/register",
        json={"username": "mallory", "email": "mallory@example.com", "password": "Passw0rd!", "is_admin": True, "id": 999},
    )
    assert created.status_code == 201
    assert created.json()["id"] != 999 and "is_admin" not in created.json()

    room = room_id_by_name(client, alice.headers, "Salle Monet")
    start, end = slot()
    response = client.post(
        "/api/bookings",
        json={"room_id": room, "start_at": start, "end_at": end, "user_id": bob.id},
        headers=alice.headers,
    )
    assert response.status_code == 201
    assert db_session.scalar(select(Booking.user_id).where(Booking.id == response.json()["id"])) == alice.id


# ------------------------------------------------------------------------------ Validation des entrées
@pytest.mark.parametrize("password", ["password", "12345678", "PASSWORD1", "password1", "Password", "Ab1"])
def test_st19_weak_passwords_are_rejected(client, db_session, password):
    """Inscription avec un mot de passe faible (courant, sans majuscule, sans chiffre, trop court...).
    Attendu : 422 et aucun compte créé."""
    assert register(client, "alice", "alice@example.com", password).status_code == 422
    assert db_session.scalar(select(func.count(User.id))) == 0


@pytest.mark.parametrize(
    "password",
    ["Aa1" + "a" * 80, "Aa1" + "é" * 40, "Aa1" + "x" * 1_000_000],
    ids=["83-octets-ascii", "83-octets-utf8", "1-Mo"],
)
def test_st20_oversized_passwords_return_422_not_500(client, password):
    """Mots de passe démesurés (83 octets, 83 octets en UTF-8, 1 Mo).
    Attendu : 422 à l'inscription ; à la connexion 401 ou 422, jamais une erreur serveur 500
    (bcrypt est limité à 72 octets : l'application doit le gérer proprement)."""
    assert register(client, "alice", "alice@example.com", password).status_code == 422
    login_status = client.post("/api/auth/login", json={"email": "alice@example.com", "password": password}).status_code
    assert login_status in (401, 422)


def test_st21_validation_errors_do_not_echo_the_password(client):
    """Inscription avec un mot de passe refusé : « motdepassefaible ».
    Attendu : la réponse 422 ne contient pas ce mot de passe (pas de fuite dans les erreurs/journaux)."""
    response = register(client, "alice", "alice@example.com", "motdepassefaible")
    assert response.status_code == 422
    assert "motdepassefaible" not in response.text


# ------------------------------------------------------------------------------ Configuration HTTP
def test_st22_cors_only_allows_configured_origins(client):
    """Requête CORS depuis un site non autorisé puis depuis le front autorisé.
    Attendu : aucun en-tête Access-Control-Allow-Origin pour le site inconnu ; présent pour le front."""
    request = {"Access-Control-Request-Method": "GET", "Access-Control-Request-Headers": "authorization"}
    evil = client.options("/api/rooms", headers={"Origin": "https://evil.example", **request})
    assert "access-control-allow-origin" not in evil.headers
    good = client.options("/api/rooms", headers={"Origin": "http://localhost:5173", **request})
    assert good.headers.get("access-control-allow-origin") == "http://localhost:5173"


def test_st23_security_headers_are_present(client):
    """En-têtes de sécurité HTTP sur une réponse de l'API.
    Attendu : nosniff, interdiction d'être affichée dans une iframe, pas de mise en cache, referrer coupé."""
    response = client.get("/api/health")
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["referrer-policy"] == "no-referrer"


def test_st24_errors_do_not_leak_internal_details(client, alice):
    """Requêtes malformées : identifiant non numérique, route inconnue, mauvaise méthode HTTP.
    Attendu : 422 / 404 / 405 propres, sans trace de pile ni détail SQL ou technique dans la réponse."""
    responses = [
        client.delete("/api/bookings/abc", headers=alice.headers),
        client.get("/api/route-inconnue", headers=alice.headers),
        client.put("/api/bookings", headers=alice.headers),
    ]
    assert [r.status_code for r in responses] == [422, 404, 405]
    for response in responses:
        body = response.text.lower()
        assert not any(word in body for word in ("traceback", "sqlalchemy", "psycopg", "postgres"))


def test_st25_secret_key_is_strong_enough():
    """Clé secrète JWT utilisée par l'application.
    Attendu : au moins 32 caractères (une clé courte rendrait les jetons devinables par force brute)."""
    assert len(config.SECRET_KEY) >= 32
