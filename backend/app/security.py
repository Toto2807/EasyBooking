"""Hachage des mots de passe (bcrypt) et jetons d'accès (JWT)."""
from datetime import datetime, timedelta, timezone
from functools import lru_cache

import bcrypt
import jwt

from . import config


def hash_password(password: str) -> str:
    return bcrypt.hashpw(
        password.encode("utf-8"), bcrypt.gensalt(rounds=config.BCRYPT_ROUNDS)
    ).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:  # hash mal formé ou mot de passe > 72 octets
        return False


@lru_cache(maxsize=1)
def dummy_hash() -> str:
    """Hash factice : permet de garder un temps de réponse similaire quand l'e-mail est inconnu."""
    return hash_password("dummy-password-for-timing")


def create_access_token(subject: int | str, expires_delta: timedelta | None = None) -> str:
    now = datetime.now(timezone.utc)
    lifetime = (
        expires_delta
        if expires_delta is not None
        else timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload = {"sub": str(subject), "iat": now, "exp": now + lifetime}
    return jwt.encode(payload, config.SECRET_KEY, algorithm=config.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    """Décode et vérifie un jeton. Lève une `jwt.PyJWTError` s'il est invalide ou expiré."""
    return jwt.decode(
        token,
        config.SECRET_KEY,
        algorithms=[config.JWT_ALGORITHM],  # liste blanche : refuse "none" et les autres algos
        options={"require": ["exp", "sub"]},
    )
