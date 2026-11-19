"""Tests d'intégration : réservations (création, conflits, liste, annulation)."""
from datetime import datetime, timedelta

from app.models import Booking
from tests.helpers import book, room_id_by_name, slot


def test_it21_create_booking(client, alice):
    """Réservation d'une chambre libre sur un créneau futur.
    Attendu : 201, réservation « confirmed » avec le nom de la chambre et les horaires demandés."""
    room = room_id_by_name(client, alice.headers, "Salle Monet")
    start, end = slot()
    response = book(client, alice, room, start, end)
    assert response.status_code == 201
    body = response.json()
    assert body["room_name"] == "Salle Monet"
    assert body["status"] == "confirmed"
    assert body["start_at"][:16] == start[:16] and body["end_at"][:16] == end[:16]


def test_it22_overlapping_booking_is_refused(client, alice, bob):
    """Réservation d'une chambre déjà prise sur un créneau qui chevauche.
    Attendu : 409 « déjà réservée » ; la première réservation reste intacte."""
    room = room_id_by_name(client, alice.headers, "Salle Monet")
    start, end = slot(hour=10, hours=2)
    assert book(client, alice, room, start, end).status_code == 201

    overlap_start, overlap_end = slot(hour=11, hours=2)
    response = book(client, bob, room, overlap_start, overlap_end)
    assert response.status_code == 409
    assert "déjà réservée" in response.json()["detail"]
    assert len(client.get("/api/bookings", headers=alice.headers).json()) == 1


def test_it23_back_to_back_bookings_are_allowed(client, alice, bob):
    """Deux réservations bout à bout (10h-12h puis 12h-13h) sur la même chambre.
    Attendu : les deux sont acceptées (201)."""
    room = room_id_by_name(client, alice.headers, "Salle Monet")
    assert book(client, alice, room, *slot(hour=10, hours=2)).status_code == 201
    assert book(client, bob, room, *slot(hour=12, hours=1)).status_code == 201


def test_it24_unknown_room_returns_404(client, alice):
    """Réservation d'une chambre qui n'existe pas.
    Attendu : 404."""
    assert book(client, alice, 9999, *slot()).status_code == 404


def test_it25_inactive_room_cannot_be_booked(client, alice):
    """Réservation de la Salle Picasso (en rénovation).
    Attendu : 409 « pas disponible à la réservation »."""
    picasso = room_id_by_name(client, alice.headers, "Salle Picasso")
    response = book(client, alice, picasso, *slot())
    assert response.status_code == 409
    assert "pas disponible" in response.json()["detail"]


def test_it26_past_or_invalid_slot_is_refused(client, alice):
    """Réservation dans le passé, avec fin avant début, ou de plus de 8 h.
    Attendu : 422 dans les trois cas."""
    room = room_id_by_name(client, alice.headers, "Salle Monet")
    assert book(client, alice, room, *slot(days=-2)).status_code == 422
    start, end = slot()
    assert book(client, alice, room, end, start).status_code == 422
    assert book(client, alice, room, *slot(hours=9)).status_code == 422


def test_it27_my_bookings_lists_only_my_bookings_newest_first(client, alice, bob):
    """Consultation de « mes réservations » alors que deux utilisateurs ont réservé.
    Attendu : chacun ne voit que les siennes, triées de la plus lointaine à la plus proche."""
    monet = room_id_by_name(client, alice.headers, "Salle Monet")
    renoir = room_id_by_name(client, alice.headers, "Salle Renoir")
    book(client, alice, monet, *slot(days=3))
    book(client, alice, renoir, *slot(days=9))
    book(client, bob, monet, *slot(days=4))

    mine = client.get("/api/bookings", headers=alice.headers).json()
    assert [b["room_name"] for b in mine] == ["Salle Renoir", "Salle Monet"]
    assert len(client.get("/api/bookings", headers=bob.headers).json()) == 1


def test_it28_cancel_booking_frees_the_slot(client, alice, bob):
    """Annulation d'une réservation puis nouvelle réservation du même créneau par un autre utilisateur.
    Attendu : annulation 200 (« cancelled ») puis réservation de Bob acceptée (201)."""
    room = room_id_by_name(client, alice.headers, "Salle Monet")
    start, end = slot()
    booking_id = book(client, alice, room, start, end).json()["id"]

    cancel = client.delete(f"/api/bookings/{booking_id}", headers=alice.headers)
    assert cancel.status_code == 200 and cancel.json()["status"] == "cancelled"
    assert book(client, bob, room, start, end).status_code == 201


def test_it29_cannot_cancel_someone_elses_booking(client, alice, bob):
    """Bob tente d'annuler la réservation d'Alice.
    Attendu : 404 et la réservation d'Alice reste confirmée."""
    room = room_id_by_name(client, alice.headers, "Salle Monet")
    booking_id = book(client, alice, room, *slot()).json()["id"]

    assert client.delete(f"/api/bookings/{booking_id}", headers=bob.headers).status_code == 404
    assert client.get("/api/bookings", headers=alice.headers).json()[0]["status"] == "confirmed"


def test_it30_cancel_twice_is_refused(client, alice):
    """Annulation d'une réservation déjà annulée.
    Attendu : 409 « déjà annulée »."""
    room = room_id_by_name(client, alice.headers, "Salle Monet")
    booking_id = book(client, alice, room, *slot()).json()["id"]
    client.delete(f"/api/bookings/{booking_id}", headers=alice.headers)
    response = client.delete(f"/api/bookings/{booking_id}", headers=alice.headers)
    assert response.status_code == 409
    assert "déjà annulée" in response.json()["detail"]


def test_it31_cannot_cancel_a_booking_already_started(client, alice, db_session):
    """Annulation d'une réservation qui a déjà commencé (insérée directement en base).
    Attendu : 409."""
    room = room_id_by_name(client, alice.headers, "Salle Monet")
    started = datetime.now() - timedelta(hours=1)
    booking = Booking(user_id=alice.id, room_id=room, start_at=started, end_at=started + timedelta(hours=3))
    db_session.add(booking)
    db_session.commit()

    response = client.delete(f"/api/bookings/{booking.id}", headers=alice.headers)
    assert response.status_code == 409


def test_it32_cancel_unknown_booking_returns_404(client, alice):
    """Annulation d'une réservation inexistante.
    Attendu : 404."""
    assert client.delete("/api/bookings/9999", headers=alice.headers).status_code == 404
