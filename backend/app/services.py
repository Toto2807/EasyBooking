"""Logique métier des réservations (détection de chevauchement)."""
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import BOOKING_CONFIRMED, Booking


def intervals_overlap(a_start: datetime, a_end: datetime, b_start: datetime, b_end: datetime) -> bool:
    """Deux créneaux se chevauchent si chacun commence avant la fin de l'autre.

    Les créneaux « bout à bout » (fin == début) ne se chevauchent pas.
    """
    return a_start < b_end and b_start < a_end


def has_conflict(db: Session, room_id: int, start_at: datetime, end_at: datetime) -> bool:
    """Vrai si une réservation confirmée de cette chambre chevauche le créneau."""
    stmt = (
        select(Booking.id)
        .where(
            Booking.room_id == room_id,
            Booking.status == BOOKING_CONFIRMED,
            Booking.start_at < end_at,
            Booking.end_at > start_at,
        )
        .limit(1)
    )
    return db.execute(stmt).first() is not None


def busy_room_ids(db: Session, start_at: datetime, end_at: datetime) -> set[int]:
    """Identifiants des chambres déjà réservées (confirmées) sur le créneau."""
    stmt = select(Booking.room_id).where(
        Booking.status == BOOKING_CONFIRMED,
        Booking.start_at < end_at,
        Booking.end_at > start_at,
    )
    return set(db.scalars(stmt).all())
