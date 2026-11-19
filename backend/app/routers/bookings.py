"""Création, consultation et annulation des réservations."""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import BOOKING_CANCELLED, BOOKING_CONFIRMED, Booking, Room, User
from ..schemas import BookingCreate, BookingOut
from ..services import has_conflict

router = APIRouter(prefix="/api/bookings", tags=["bookings"])


@router.post("", response_model=BookingOut, status_code=201)
def create_booking(
    payload: BookingCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Verrou de ligne sur la chambre : deux réservations simultanées de la même chambre
    # sont traitées l'une après l'autre (pas de double réservation).
    room = db.scalar(select(Room).where(Room.id == payload.room_id).with_for_update())
    if room is None:
        raise HTTPException(status_code=404, detail="Chambre introuvable")
    if not room.is_active:
        raise HTTPException(status_code=409, detail="Cette chambre n'est pas disponible à la réservation")
    if has_conflict(db, room.id, payload.start_at, payload.end_at):
        raise HTTPException(status_code=409, detail="Cette chambre est déjà réservée sur ce créneau")

    booking = Booking(
        user_id=user.id,  # toujours l'utilisateur authentifié, jamais une valeur du client
        room_id=room.id,
        start_at=payload.start_at,
        end_at=payload.end_at,
        status=BOOKING_CONFIRMED,
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return booking


@router.get("", response_model=list[BookingOut])
def my_bookings(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Réservations de l'utilisateur connecté (passées et à venir), les plus récentes d'abord."""
    stmt = select(Booking).where(Booking.user_id == user.id).order_by(Booking.start_at.desc())
    return db.scalars(stmt).unique().all()


@router.delete("/{booking_id}", response_model=BookingOut)
def cancel_booking(
    booking_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    booking = db.get(Booking, booking_id)
    # 404 (et non 403) si la réservation appartient à quelqu'un d'autre : on ne révèle pas son existence.
    if booking is None or booking.user_id != user.id:
        raise HTTPException(status_code=404, detail="Réservation introuvable")
    if booking.status == BOOKING_CANCELLED:
        raise HTTPException(status_code=409, detail="Cette réservation est déjà annulée")
    if booking.start_at <= datetime.now():
        raise HTTPException(status_code=409, detail="Une réservation commencée ou passée ne peut plus être annulée")

    booking.status = BOOKING_CANCELLED
    db.commit()
    db.refresh(booking)
    return booking
