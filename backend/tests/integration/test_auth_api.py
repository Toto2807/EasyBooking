"""Tests d'intégration : inscription, connexion, profil (API + PostgreSQL)."""
from sqlalchemy import select

from app.models import User
from tests.helpers import PASSWORD, login, register


def test_it01_register_creates_account(client, db_session):
    """Inscription avec des données valides.
    Attendu : 201, l'utilisateur est renvoyé sans mot de passe et enregistré en base."""
    response = register(client, "alice", "alice@example.com")
    assert response.status_code == 201
    body = response.json()
    assert body["username"] == "alice" and body["email"] == "alice@example.com"
    assert "password" not in body and "password_hash" not in body
    assert db_session.scalar(select(User).where(User.email == "alice@example.com")) is not None


def test_it02_register_duplicate_email_is_refused(client):
    """Inscription avec un e-mail déjà utilisé.
    Attendu : 409 avec un message explicite."""
    register(client, "alice", "alice@example.com")
    response = register(client, "alice2", "ALICE@example.com")  # même e-mail, casse différente
    assert response.status_code == 409
    assert "e-mail" in response.json()["detail"]


def test_it03_register_duplicate_username_is_refused(client):
    """Inscription avec un nom d'utilisateur déjà pris (casse différente).
    Attendu : 409 avec un message explicite."""
    register(client, "alice", "alice@example.com")
    response = register(client, "ALICE", "autre@example.com")
    assert response.status_code == 409
    assert "nom d'utilisateur" in response.json()["detail"]


def test_it04_register_invalid_payload_returns_field_errors(client):
    """Inscription avec e-mail invalide, mot de passe faible et nom trop court.
    Attendu : 422 avec une liste d'erreurs {field, message} et aucun compte créé."""
    response = client.post(
        "/api/auth/register", json={"username": "a", "email": "oups", "password": "faible"}
    )
    assert response.status_code == 422
    fields = {error["field"] for error in response.json()["detail"]}
    assert {"username", "email", "password"} <= fields


def test_it05_login_returns_working_token(client):
    """Connexion avec les bons identifiants.
    Attendu : 200, un jeton d'accès, et ce jeton permet d'appeler une route protégée."""
    register(client, "alice", "alice@example.com")
    response = login(client, "alice@example.com", PASSWORD)
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer" and body["user"]["username"] == "alice"
    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {body['access_token']}"})
    assert me.status_code == 200


def test_it06_login_wrong_password_is_refused(client):
    """Connexion avec un mauvais mot de passe.
    Attendu : 401 avec un message d'erreur."""
    register(client, "alice", "alice@example.com")
    response = login(client, "alice@example.com", "MauvaisMdp1")
    assert response.status_code == 401
    assert response.json()["detail"] == "E-mail ou mot de passe incorrect"


def test_it07_login_unknown_email_is_refused(client):
    """Connexion avec un e-mail inconnu.
    Attendu : 401 avec exactement le même message que pour un mauvais mot de passe."""
    response = login(client, "inconnu@example.com", PASSWORD)
    assert response.status_code == 401
    assert response.json()["detail"] == "E-mail ou mot de passe incorrect"


def test_it08_login_is_case_insensitive_on_email(client):
    """Connexion avec l'e-mail saisi en majuscules.
    Attendu : 200 (l'e-mail est normalisé)."""
    register(client, "alice", "alice@example.com")
    assert login(client, "  ALICE@Example.COM ", PASSWORD).status_code == 200


def test_it09_me_returns_current_user(client, alice):
    """Appel de /api/auth/me avec un jeton valide.
    Attendu : 200 et les informations de l'utilisateur connecté."""
    response = client.get("/api/auth/me", headers=alice.headers)
    assert response.status_code == 200
    assert response.json() == {"id": alice.id, "username": "alice", "email": "alice@example.com"}


def test_it10_me_without_token_is_refused(client):
    """Appel de /api/auth/me sans jeton.
    Attendu : 401."""
    assert client.get("/api/auth/me").status_code == 401
