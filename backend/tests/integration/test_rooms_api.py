"""Tests d'intégration : liste des chambres, filtres, disponibilités."""
from tests.helpers import book, room_id_by_name, slot


def _by_name(rooms: list[dict]) -> dict:
    return {room["name"]: room for room in rooms}


def test_it11_list_rooms_returns_seeded_rooms(client, alice):
    """Liste des chambres juste après installation.
    Attendu : 200, les 8 chambres de départ triées par nom, avec tous les champs."""
    response = client.get("/api/rooms", headers=alice.headers)
    assert response.status_code == 200
    rooms = response.json()
    assert len(rooms) == 8
    assert [r["name"] for r in rooms] == sorted(r["name"] for r in rooms)
    assert {"id", "name", "capacity", "location", "description", "amenities", "is_active", "available"} <= set(rooms[0])


def test_it12_filter_by_min_capacity(client, alice):
    """Filtre par capacité minimale (10 personnes).
    Attendu : uniquement les chambres de 10 places ou plus."""
    rooms = client.get("/api/rooms", params={"min_capacity": 10}, headers=alice.headers).json()
    assert {r["name"] for r in rooms} == {"Salle Cézanne", "Salle Van Gogh", "Auditorium Rodin"}
    assert all(r["capacity"] >= 10 for r in rooms)


def test_it13_filter_by_amenity_is_case_insensitive(client, alice):
    """Filtre par équipement « visioconférence » (en minuscules).
    Attendu : les chambres équipées de Visioconférence uniquement."""
    rooms = client.get("/api/rooms", params={"amenity": "visioconférence"}, headers=alice.headers).json()
    assert {r["name"] for r in rooms} == {"Salle Degas", "Salle Van Gogh", "Auditorium Rodin"}


def test_it14_combined_filters(client, alice):
    """Filtres combinés : capacité 6 à 10 et équipement « Projecteur ».
    Attendu : seule la Salle Cézanne correspond."""
    rooms = client.get(
        "/api/rooms",
        params={"min_capacity": 6, "max_capacity": 10, "amenity": "Projecteur"},
        headers=alice.headers,
    ).json()
    assert [r["name"] for r in rooms] == ["Salle Cézanne"]


def test_it15_inactive_room_is_not_available(client, alice):
    """Chambre en rénovation (is_active = false).
    Attendu : elle apparaît dans la liste mais available = false."""
    rooms = _by_name(client.get("/api/rooms", headers=alice.headers).json())
    assert rooms["Salle Picasso"]["is_active"] is False
    assert rooms["Salle Picasso"]["available"] is False
    assert rooms["Salle Monet"]["available"] is True


def test_it16_availability_reflects_bookings_for_a_slot(client, alice, bob):
    """Liste des chambres pour un créneau après une réservation de la Salle Monet.
    Attendu : Monet available = false sur ce créneau, true sur un autre ; available_only la masque."""
    monet = room_id_by_name(client, alice.headers, "Salle Monet")
    start, end = slot(days=5, hour=14, hours=2)
    assert book(client, alice, monet, start, end).status_code == 201

    busy = _by_name(client.get("/api/rooms", params={"start": start, "end": end}, headers=bob.headers).json())
    assert busy["Salle Monet"]["available"] is False
    assert busy["Salle Renoir"]["available"] is True

    other_start, other_end = slot(days=5, hour=17, hours=1)
    free = _by_name(
        client.get("/api/rooms", params={"start": other_start, "end": other_end}, headers=bob.headers).json()
    )
    assert free["Salle Monet"]["available"] is True

    only = client.get(
        "/api/rooms", params={"start": start, "end": end, "available_only": True}, headers=bob.headers
    ).json()
    assert "Salle Monet" not in [r["name"] for r in only]


def test_it17_amenities_endpoint_lists_unique_sorted_values(client, alice):
    """Liste des équipements disponibles (alimente le filtre du front).
    Attendu : valeurs uniques triées, contenant Wi-Fi et Projecteur."""
    amenities = client.get("/api/rooms/amenities", headers=alice.headers).json()
    assert amenities == sorted(set(amenities))
    assert {"Wi-Fi", "Projecteur", "Visioconférence"} <= set(amenities)


def test_it18_room_availability_endpoint_returns_busy_slots(client, alice):
    """Créneaux occupés d'une chambre pour une journée donnée.
    Attendu : les réservations confirmées du jour, triées, sans information sur les utilisateurs."""
    renoir = room_id_by_name(client, alice.headers, "Salle Renoir")
    morning = slot(days=6, hour=9, hours=1)
    afternoon = slot(days=6, hour=15, hours=2)
    book(client, alice, renoir, *afternoon)
    book(client, alice, renoir, *morning)
    day = morning[0][:10]

    response = client.get(f"/api/rooms/{renoir}/availability", params={"date": day}, headers=alice.headers)
    assert response.status_code == 200
    slots = response.json()["busy_slots"]
    assert [s["start_at"][:16] for s in slots] == [morning[0][:16], afternoon[0][:16]]
    assert set(slots[0]) == {"start_at", "end_at"}


def test_it19_unknown_room_returns_404(client, alice):
    """Consultation d'une chambre inexistante.
    Attendu : 404 pour la fiche et pour ses disponibilités."""
    assert client.get("/api/rooms/9999", headers=alice.headers).status_code == 404
    assert client.get("/api/rooms/9999/availability", params={"date": "2030-01-01"}, headers=alice.headers).status_code == 404


def test_it20_slot_filter_requires_both_bounds(client, alice):
    """Filtre de créneau avec seulement « start », une fin avant le début, ou des dates avec fuseau horaire.
    Attendu : 422 dans les trois cas."""
    start, end = slot()
    assert client.get("/api/rooms", params={"start": start}, headers=alice.headers).status_code == 422
    assert client.get("/api/rooms", params={"start": end, "end": start}, headers=alice.headers).status_code == 422
    with_timezone = {"start": start + "+00:00", "end": end + "+00:00"}
    assert client.get("/api/rooms", params=with_timezone, headers=alice.headers).status_code == 422


def test_it34_get_single_room(client, alice):
    """Consultation de la fiche d'une chambre existante (Salle Cézanne).
    Attendu : 200 avec ses détails (capacité 10, équipements, disponible)."""
    room_id = room_id_by_name(client, alice.headers, "Salle Cézanne")
    response = client.get(f"/api/rooms/{room_id}", headers=alice.headers)
    assert response.status_code == 200
    room = response.json()
    assert room["name"] == "Salle Cézanne" and room["capacity"] == 10
    assert "Projecteur" in room["amenities"] and room["available"] is True
