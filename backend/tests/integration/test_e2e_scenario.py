"""Test d'intégration : parcours complet d'un utilisateur, comme dans l'application."""
from tests.helpers import PASSWORD, slot


def test_it33_full_user_journey(client):
    """Parcours complet : inscription → connexion → liste des chambres → réservation → mes réservations → annulation.
    Attendu : chaque étape réussit et l'état final montre la réservation annulée."""
    # 1. Inscription
    created = client.post(
        "/api/auth/register",
        json={"username": "camille", "email": "camille@example.com", "password": PASSWORD},
    )
    assert created.status_code == 201

    # 2. Connexion
    token = client.post(
        "/api/auth/login", json={"email": "camille@example.com", "password": PASSWORD}
    ).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 3. Chambres disponibles pour 6 personnes sur un créneau
    start, end = slot(days=10, hour=9, hours=3)
    rooms = client.get(
        "/api/rooms",
        params={"min_capacity": 6, "start": start, "end": end, "available_only": True},
        headers=headers,
    ).json()
    assert rooms and all(r["capacity"] >= 6 and r["available"] for r in rooms)

    # 4. Réservation de la première chambre proposée
    booking = client.post(
        "/api/bookings",
        json={"room_id": rooms[0]["id"], "start_at": start, "end_at": end},
        headers=headers,
    )
    assert booking.status_code == 201

    # 5. La chambre n'est plus proposée sur ce créneau
    again = client.get(
        "/api/rooms",
        params={"min_capacity": 6, "start": start, "end": end, "available_only": True},
        headers=headers,
    ).json()
    assert rooms[0]["id"] not in [r["id"] for r in again]

    # 6. Mes réservations puis annulation
    mine = client.get("/api/bookings", headers=headers).json()
    assert len(mine) == 1 and mine[0]["status"] == "confirmed"
    assert client.delete(f"/api/bookings/{mine[0]['id']}", headers=headers).status_code == 200
    assert client.get("/api/bookings", headers=headers).json()[0]["status"] == "cancelled"
