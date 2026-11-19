"""Liste des chambres, filtres et disponibilités."""
from datetime import date as date_type
from datetime import datetime, time, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import BOOKING_CONFIRMED, Booking, Room
from ..schemas import BusySlot, RoomAvailability, RoomOut
from ..services import busy_room_ids

router = APIRouter(prefix="/api/rooms", tags=["rooms"], dependencies=[Depends(get_current_user)])


def _invalid(field: str, message: str) -> HTTPException:
    return HTTPException(status_code=422, detail=[{"field": field, "message": message}])


def _to_out(room: Room, busy_ids: set[int]) -> RoomOut:
    return RoomOut(
        id=room.id,
        name=room.name,
        capacity=room.capacity,
        location=room.location,
        description=room.description,
        amenities=list(room.amenities or []),
        is_active=room.is_active,
        available=room.is_active and room.id not in busy_ids,
    )


@router.get("", response_model=list[RoomOut])
def list_rooms(
    min_capacity: int | None = Query(None, ge=1, le=1000),
    max_capacity: int | None = Query(None, ge=1, le=1000),
    amenity: str | None = Query(None, max_length=50),
    start: datetime | None = Query(None, description="Début du créneau (ISO 8601, heure locale)"),
    end: datetime | None = Query(None, description="Fin du créneau (ISO 8601, heure locale)"),
    available_only: bool = False,
    db: Session = Depends(get_db),
):
    """Liste des chambres. Avec `start` et `end`, `available` tient compte des réservations."""
    if (start is None) != (end is None):
        raise _invalid("start", "Les paramètres 'start' et 'end' doivent être fournis ensemble")
    busy_ids: set[int] = set()
    if start is not None and end is not None:
        if start.tzinfo is not None or end.tzinfo is not None:
            raise _invalid("start", "Les dates doivent être envoyées sans fuseau horaire")
        if end <= start:
            raise _invalid("end", "L'heure de fin doit être après l'heure de début")
        busy_ids = busy_room_ids(db, start, end)

    stmt = select(Room).order_by(Room.name)
    if min_capacity is not None:
        stmt = stmt.where(Room.capacity >= min_capacity)
    if max_capacity is not None:
        stmt = stmt.where(Room.capacity <= max_capacity)
    rooms = db.scalars(stmt).all()

    if amenity:
        wanted = amenity.strip().lower()
        rooms = [r for r in rooms if wanted in [a.lower() for a in (r.amenities or [])]]

    result = [_to_out(room, busy_ids) for room in rooms]
    if available_only:
        result = [room for room in result if room.available]
    return result


# Doit être déclarée AVANT "/{room_id}" sinon "amenities" serait lu comme un identifiant.
@router.get("/amenities", response_model=list[str])
def list_amenities(db: Session = Depends(get_db)):
    """Liste des équipements existants (pour alimenter le filtre du front)."""
    names: set[str] = set()
    for amenities in db.scalars(select(Room.amenities)).all():
        names.update(amenities or [])
    return sorted(names)


@router.get("/{room_id}", response_model=RoomOut)
def get_room(room_id: int, db: Session = Depends(get_db)):
    room = db.get(Room, room_id)
    if room is None:
        raise HTTPException(status_code=404, detail="Chambre introuvable")
    return _to_out(room, set())


@router.get("/{room_id}/availability", response_model=RoomAvailability)
def room_availability(
    room_id: int,
    day: date_type = Query(..., alias="date", description="Jour (AAAA-MM-JJ)"),
    db: Session = Depends(get_db),
):
    """Créneaux déjà réservés pour une chambre sur une journée (sans infos sur les utilisateurs)."""
    if db.get(Room, room_id) is None:
        raise HTTPException(status_code=404, detail="Chambre introuvable")
    day_start = datetime.combine(day, time.min)
    day_end = day_start + timedelta(days=1)
    stmt = (
        select(Booking)
        .where(
            Booking.room_id == room_id,
            Booking.status == BOOKING_CONFIRMED,
            Booking.start_at < day_end,
            Booking.end_at > day_start,
        )
        .order_by(Booking.start_at)
    )
    slots = [BusySlot(start_at=b.start_at, end_at=b.end_at) for b in db.scalars(stmt).all()]
    return RoomAvailability(room_id=room_id, date=day, busy_slots=slots)
