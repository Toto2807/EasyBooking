"""Tests unitaires : règles de validation des entrées (app/schemas.py)."""
from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from app.schemas import BookingCreate, UserCreate

VALID_USER = {"username": "alice", "email": "Alice@Example.com", "password": "Passw0rd!"}


def _future(hours_from_now: int = 48) -> datetime:
    return (datetime.now() + timedelta(hours=hours_from_now)).replace(minute=0, second=0, microsecond=0)


def test_ut11_valid_user_is_accepted_and_email_lowercased():
    """Inscription avec des données valides (e-mail avec majuscules).
    Attendu : la validation passe et l'e-mail est normalisé en minuscules."""
    user = UserCreate(**VALID_USER)
    assert user.email == "alice@example.com"
    assert user.username == "alice"


@pytest.mark.parametrize("email", ["pas-un-email", "a@b", "@example.com", "alice@", "", "a b@example.com"])
def test_ut12_invalid_email_is_rejected(email):
    """Inscription avec un e-mail au mauvais format.
    Attendu : ValidationError."""
    with pytest.raises(ValidationError):
        UserCreate(**{**VALID_USER, "email": email})


def test_ut13_short_password_is_rejected():
    """Mot de passe de 7 caractères (minimum exigé : 8).
    Attendu : ValidationError."""
    with pytest.raises(ValidationError):
        UserCreate(**{**VALID_USER, "password": "Abcde1x"})


@pytest.mark.parametrize(
    "password",
    ["alllowercase1", "ALLUPPERCASE1", "NoDigitsHere"],
    ids=["sans-majuscule", "sans-minuscule", "sans-chiffre"],
)
def test_ut14_password_missing_character_class_is_rejected(password):
    """Mot de passe long mais sans majuscule / sans minuscule / sans chiffre.
    Attendu : ValidationError."""
    with pytest.raises(ValidationError):
        UserCreate(**{**VALID_USER, "password": password})


@pytest.mark.parametrize("username", ["ab", "a" * 31, "al ice", "alice<script>", "al;ice", "é"])
def test_ut15_invalid_username_is_rejected(username):
    """Nom d'utilisateur trop court, trop long ou avec des caractères interdits.
    Attendu : ValidationError."""
    with pytest.raises(ValidationError):
        UserCreate(**{**VALID_USER, "username": username})


def test_ut16_unknown_fields_are_ignored():
    """Inscription avec des champs supplémentaires non prévus (is_admin, id).
    Attendu : ils sont ignorés et n'apparaissent pas dans le modèle."""
    user = UserCreate(**VALID_USER, is_admin=True, id=999)
    assert not hasattr(user, "is_admin")
    assert not hasattr(user, "id")


def test_ut17_valid_booking_is_accepted_and_seconds_dropped():
    """Réservation valide (début avec des secondes).
    Attendu : la validation passe et les secondes sont ramenées à 0."""
    start = _future() + timedelta(seconds=37)
    booking = BookingCreate(room_id=1, start_at=start, end_at=start + timedelta(hours=1))
    assert booking.start_at.second == 0
    assert booking.end_at > booking.start_at


@pytest.mark.parametrize("delta_hours", [0, -1], ids=["fin-egale-debut", "fin-avant-debut"])
def test_ut18_end_not_after_start_is_rejected(delta_hours):
    """Heure de fin égale ou antérieure à l'heure de début.
    Attendu : ValidationError."""
    start = _future()
    with pytest.raises(ValidationError):
        BookingCreate(room_id=1, start_at=start, end_at=start + timedelta(hours=delta_hours))


def test_ut19_booking_longer_than_max_duration_is_rejected():
    """Réservation de 9 heures (maximum autorisé : 8 h).
    Attendu : ValidationError."""
    start = _future()
    with pytest.raises(ValidationError):
        BookingCreate(room_id=1, start_at=start, end_at=start + timedelta(hours=9))


def test_ut20_booking_in_the_past_is_rejected():
    """Réservation qui commence hier.
    Attendu : ValidationError."""
    start = datetime.now() - timedelta(days=1)
    with pytest.raises(ValidationError):
        BookingCreate(room_id=1, start_at=start, end_at=start + timedelta(hours=1))


def test_ut21_timezone_aware_datetime_is_rejected():
    """Dates envoyées avec un fuseau horaire (UTC).
    Attendu : ValidationError (l'API n'accepte que l'heure locale sans fuseau)."""
    start = datetime.now(timezone.utc) + timedelta(days=2)
    with pytest.raises(ValidationError):
        BookingCreate(room_id=1, start_at=start, end_at=start + timedelta(hours=1))


def test_ut22_invalid_room_id_is_rejected():
    """Réservation avec un identifiant de chambre négatif ou nul.
    Attendu : ValidationError."""
    start = _future()
    for bad_id in (0, -3):
        with pytest.raises(ValidationError):
            BookingCreate(room_id=bad_id, start_at=start, end_at=start + timedelta(hours=1))
