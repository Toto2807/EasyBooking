"""Tests unitaires : hachage des mots de passe et jetons JWT (app/security.py)."""
import base64
import json
from datetime import datetime, timedelta, timezone

import jwt
import pytest

from app import config
from app.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_ut01_hash_password_is_not_plaintext():
    """Le hash d'un mot de passe ne contient pas le mot de passe en clair.
    Attendu : le hash est différent du mot de passe et commence par le préfixe bcrypt '$2'."""
    hashed = hash_password("Passw0rd!")
    assert hashed != "Passw0rd!"
    assert "Passw0rd!" not in hashed
    assert hashed.startswith("$2")


def test_ut02_verify_password_accepts_correct_password():
    """Vérification d'un mot de passe correct.
    Attendu : verify_password renvoie True."""
    assert verify_password("Passw0rd!", hash_password("Passw0rd!")) is True


def test_ut03_verify_password_rejects_wrong_password():
    """Vérification d'un mauvais mot de passe.
    Attendu : verify_password renvoie False."""
    assert verify_password("MauvaisMdp1", hash_password("Passw0rd!")) is False


def test_ut04_hash_is_salted():
    """Deux hachages du même mot de passe.
    Attendu : les deux hashs sont différents (sel aléatoire) mais valident tous les deux."""
    first, second = hash_password("Passw0rd!"), hash_password("Passw0rd!")
    assert first != second
    assert verify_password("Passw0rd!", first) and verify_password("Passw0rd!", second)


@pytest.mark.parametrize("bad_hash", ["", "pas-un-hash", "$2b$04$tropcourt"])
def test_ut05_verify_password_with_malformed_hash_returns_false(bad_hash):
    """Vérification contre un hash mal formé (donnée corrompue en base).
    Attendu : renvoie False, sans lever d'exception."""
    assert verify_password("Passw0rd!", bad_hash) is False


def test_ut06_access_token_contains_subject_and_expiry():
    """Création d'un jeton d'accès pour l'utilisateur 42.
    Attendu : le jeton décodé contient sub='42' et une date d'expiration dans le futur."""
    payload = decode_access_token(create_access_token(42))
    assert payload["sub"] == "42"
    assert payload["exp"] > datetime.now(timezone.utc).timestamp()


def test_ut07_expired_token_is_rejected():
    """Décodage d'un jeton déjà expiré.
    Attendu : jwt.ExpiredSignatureError."""
    token = create_access_token(1, expires_delta=timedelta(seconds=-5))
    with pytest.raises(jwt.ExpiredSignatureError):
        decode_access_token(token)


def test_ut08_tampered_token_is_rejected():
    """Jeton dont le contenu (sub) a été modifié sans re-signer.
    Attendu : jwt.InvalidSignatureError."""
    header, payload, signature = create_access_token(1).split(".")
    data = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
    data["sub"] = "2"
    forged = base64.urlsafe_b64encode(json.dumps(data).encode()).decode().rstrip("=")
    with pytest.raises(jwt.InvalidSignatureError):
        decode_access_token(f"{header}.{forged}.{signature}")


def test_ut09_token_signed_with_another_key_is_rejected():
    """Jeton signé avec une autre clé secrète.
    Attendu : jwt.InvalidSignatureError."""
    exp = datetime.now(timezone.utc) + timedelta(minutes=5)
    token = jwt.encode({"sub": "1", "exp": exp}, "une-autre-cle-secrete-0123456789abcdef", algorithm="HS256")
    with pytest.raises(jwt.InvalidSignatureError):
        decode_access_token(token)


def test_ut10_token_without_expiry_is_rejected():
    """Jeton valide mais sans date d'expiration (donc éternel).
    Attendu : jwt.MissingRequiredClaimError."""
    token = jwt.encode({"sub": "1"}, config.SECRET_KEY, algorithm=config.JWT_ALGORITHM)
    with pytest.raises(jwt.MissingRequiredClaimError):
        decode_access_token(token)
