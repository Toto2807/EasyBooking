"""Tests de performance et de charge (serveur HTTP réel + PostgreSQL).

Les seuils sont volontairement larges pour rester stables sur un ordinateur portable.
Sur une machine lente, multipliez-les : PERF_BUDGET_FACTOR=3 pytest tests/performance
(Remarque : le coût de bcrypt est réduit à 4 dans les tests ; en production il est de 12.)
"""
import os
import statistics
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta

import httpx

from app.database import SessionLocal
from app.models import Booking, Room
from tests.helpers import PASSWORD, create_account, slot

FACTOR = float(os.getenv("PERF_BUDGET_FACTOR", "1"))


# ------------------------------------------------------------------------------------- Outils
def timings(call, repeat: int) -> list[float]:
    """Exécute `call` plusieurs fois et renvoie les durées en secondes."""
    durations = []
    for _ in range(repeat):
        started = time.perf_counter()
        call()
        durations.append(time.perf_counter() - started)
    return durations


def p95(values: list[float]) -> float:
    ordered = sorted(values)
    return ordered[max(0, int(len(ordered) * 0.95) - 1)]


def stats(values: list[float]) -> str:
    """Résumé des mesures, repris dans la fiche de tests (propriété « mesure » du rapport JUnit)."""
    return (
        f"p95 {p95(values) * 1000:.0f} ms, moyenne {statistics.mean(values) * 1000:.0f} ms, "
        f"max {max(values) * 1000:.0f} ms ({len(values)} appels)"
    )


def fill_rooms(count: int) -> list[int]:
    """Ajoute `count` chambres directement en base (plus rapide que par l'API)."""
    amenities = ["Wi-Fi", "Projecteur", "Visioconférence", "Tableau blanc", "Écran"]
    with SessionLocal() as db:
        rooms = [
            Room(name=f"Salle perf {i}", capacity=2 + i % 30, location="Perf", description="",
                 amenities=amenities[: 1 + i % 5])
            for i in range(count)
        ]
        db.add_all(rooms)
        db.commit()
        return [room.id for room in rooms]


def fill_bookings(user_id: int, room_ids: list[int], count: int) -> None:
    """Ajoute `count` réservations sans conflit (1 h, à 9 h, sur plusieurs jours et chambres)."""
    base = (datetime.now() + timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0)
    with SessionLocal() as db:
        db.add_all(
            Booking(
                user_id=user_id,
                room_id=room_ids[i % len(room_ids)],
                start_at=base + timedelta(days=i // len(room_ids)),
                end_at=base + timedelta(days=i // len(room_ids), hours=1),
            )
            for i in range(count)
        )
        db.commit()


def new_account(http: httpx.Client, name: str):
    """Inscrit + connecte un utilisateur via l'API HTTP réelle."""
    return create_account(http, name)


# --------------------------------------------------------------------------- Temps de réponse
def test_pt01_health_endpoint_latency(http, record_property):
    """100 appels séquentiels à /api/health (requête + connexion PostgreSQL).
    Attendu : tous 200 et p95 < 100 ms."""
    durations = timings(lambda: http.get("/api/health").raise_for_status(), 100)
    record_property("mesure", stats(durations))
    assert p95(durations) < 0.1 * FACTOR, stats(durations)


def test_pt02_login_latency(http, record_property):
    """20 connexions séquentielles (vérification du hash + création du jeton).
    Attendu : tous 200 et moyenne < 300 ms."""
    http.post("/api/auth/register", json={"username": "perf", "email": "perf@example.com", "password": PASSWORD})
    call = lambda: http.post("/api/auth/login", json={"email": "perf@example.com", "password": PASSWORD}).raise_for_status()
    durations = timings(call, 20)
    record_property("mesure", stats(durations))
    assert statistics.mean(durations) < 0.3 * FACTOR, stats(durations)


def test_pt03_list_200_rooms_latency(http, record_property):
    """30 listes de chambres avec 208 chambres en base.
    Attendu : tous 200 et p95 < 250 ms."""
    fill_rooms(200)
    account = new_account(http, "alice")
    durations = timings(lambda: http.get("/api/rooms", headers=account.headers).raise_for_status(), 30)
    record_property("mesure", stats(durations))
    assert p95(durations) < 0.25 * FACTOR, stats(durations)


def test_pt04_filtered_search_with_bookings_latency(http, record_property):
    """30 recherches filtrées (capacité + équipement + créneau) avec 208 chambres et 300 réservations.
    Attendu : tous 200 et p95 < 300 ms."""
    room_ids = fill_rooms(200)
    account = new_account(http, "alice")
    fill_bookings(account.id, room_ids, 300)
    day = datetime.now() + timedelta(days=1)
    params = {
        "min_capacity": 4,
        "amenity": "Wi-Fi",
        "start": day.replace(hour=9, minute=0, second=0, microsecond=0).isoformat(),
        "end": day.replace(hour=10, minute=0, second=0, microsecond=0).isoformat(),
    }
    durations = timings(lambda: http.get("/api/rooms", params=params, headers=account.headers).raise_for_status(), 30)
    record_property("mesure", stats(durations))
    assert p95(durations) < 0.3 * FACTOR, stats(durations)


def test_pt05_create_50_bookings_sequentially(http, record_property):
    """50 réservations successives (verrou de la chambre + contrôle de conflit + insertion).
    Attendu : toutes en 201 et moyenne < 150 ms."""
    account = new_account(http, "alice")
    room_ids = [room["id"] for room in http.get("/api/rooms", headers=account.headers).json() if room["is_active"]]
    counter = iter(range(50))

    def create():
        i = next(counter)
        start, end = slot(days=2 + i // len(room_ids), hour=8, hours=1)
        response = http.post(
            "/api/bookings",
            json={"room_id": room_ids[i % len(room_ids)], "start_at": start, "end_at": end},
            headers=account.headers,
        )
        assert response.status_code == 201, response.text

    durations = timings(create, 50)
    record_property("mesure", stats(durations))
    assert statistics.mean(durations) < 0.15 * FACTOR, stats(durations)


def test_pt06_list_500_bookings_latency(http, record_property):
    """20 consultations de « mes réservations » alors que l'utilisateur en a 500.
    Attendu : 500 réservations renvoyées à chaque fois et p95 < 400 ms."""
    account = new_account(http, "alice")
    room_ids = [room["id"] for room in http.get("/api/rooms", headers=account.headers).json()]
    fill_bookings(account.id, room_ids, 500)

    def call():
        response = http.get("/api/bookings", headers=account.headers)
        assert response.status_code == 200 and len(response.json()) == 500

    durations = timings(call, 20)
    record_property("mesure", stats(durations))
    assert p95(durations) < 0.4 * FACTOR, stats(durations)


def test_pt07_room_availability_latency(http, record_property):
    """30 consultations des créneaux occupés d'une chambre qui a 100 réservations (une par jour).
    Attendu : tous 200 et p95 < 200 ms."""
    account = new_account(http, "alice")
    room_id = http.get("/api/rooms", headers=account.headers).json()[0]["id"]
    fill_bookings(account.id, [room_id], 100)
    day = (datetime.now() + timedelta(days=1)).date().isoformat()
    call = lambda: http.get(f"/api/rooms/{room_id}/availability", params={"date": day}, headers=account.headers).raise_for_status()
    durations = timings(call, 30)
    record_property("mesure", stats(durations))
    assert p95(durations) < 0.2 * FACTOR, stats(durations)


def test_pt08_register_30_users_sequentially(http, record_property):
    """30 inscriptions successives (validation + hachage bcrypt + insertion).
    Attendu : toutes en 201 et moyenne < 300 ms."""
    counter = iter(range(30))

    def register():
        i = next(counter)
        response = http.post(
            "/api/auth/register",
            json={"username": f"user{i}", "email": f"user{i}@example.com", "password": PASSWORD},
        )
        assert response.status_code == 201

    durations = timings(register, 30)
    record_property("mesure", stats(durations))
    assert statistics.mean(durations) < 0.3 * FACTOR, stats(durations)


# ------------------------------------------------------------------------- Charge & concurrence
def test_pt09_throughput_under_20_concurrent_users(http, live_server, record_property):
    """300 listes de chambres envoyées par 20 utilisateurs simultanés.
    Attendu : 0 erreur, durée totale < 15 s (soit plus de 20 requêtes/seconde)."""
    account = new_account(http, "alice")

    def call(_):
        with httpx.Client(base_url=live_server, timeout=30) as client:
            return [client.get("/api/rooms", headers=account.headers).status_code for _ in range(15)]

    started = time.perf_counter()
    with ThreadPoolExecutor(max_workers=20) as pool:
        statuses = [status for chunk in pool.map(call, range(20)) for status in chunk]
    elapsed = time.perf_counter() - started

    record_property("mesure", f"300 requêtes en {elapsed:.2f} s, soit {300 / elapsed:.0f} requêtes/s")
    assert len(statuses) == 300
    assert set(statuses) == {200}
    assert elapsed < 15 * FACTOR, f"{300 / elapsed:.0f} requêtes/s"


def test_pt10_concurrent_bookings_of_same_slot_never_double_book(http, live_server, record_property):
    """20 utilisateurs réservent EN MÊME TEMPS la même chambre sur le même créneau.
    Attendu : exactement 1 réservation acceptée (201), 19 refusées (409), aucune erreur serveur."""
    accounts = [new_account(http, f"user{i}") for i in range(20)]
    room_id = http.get("/api/rooms", headers=accounts[0].headers).json()[0]["id"]
    start, end = slot(days=3, hour=10, hours=2)
    barrier = threading.Barrier(len(accounts))

    def attempt(account):
        with httpx.Client(base_url=live_server, timeout=30) as client:
            barrier.wait()  # tous partent au même instant
            return client.post(
                "/api/bookings",
                json={"room_id": room_id, "start_at": start, "end_at": end},
                headers=account.headers,
            ).status_code

    with ThreadPoolExecutor(max_workers=len(accounts)) as pool:
        statuses = list(pool.map(attempt, accounts))

    record_property("mesure", f"{statuses.count(201)} acceptée(s) (201), {statuses.count(409)} refusée(s) (409)")
    assert sorted(statuses) == [201] + [409] * 19, statuses
    with SessionLocal() as db:
        assert db.query(Booking).filter(Booking.room_id == room_id).count() == 1


def test_pt11_concurrent_bookings_of_different_slots_all_succeed(http, live_server, record_property):
    """20 utilisateurs réservent EN MÊME TEMPS la même chambre sur 20 créneaux différents.
    Attendu : les 20 réservations sont acceptées (201), sans blocage ni erreur."""
    accounts = [new_account(http, f"user{i}") for i in range(20)]
    room_id = http.get("/api/rooms", headers=accounts[0].headers).json()[0]["id"]
    barrier = threading.Barrier(len(accounts))

    def attempt(item):
        i, account = item
        start, end = slot(days=2 + i, hour=10, hours=1)
        with httpx.Client(base_url=live_server, timeout=30) as client:
            barrier.wait()
            return client.post(
                "/api/bookings",
                json={"room_id": room_id, "start_at": start, "end_at": end},
                headers=account.headers,
            ).status_code

    with ThreadPoolExecutor(max_workers=len(accounts)) as pool:
        statuses = list(pool.map(attempt, enumerate(accounts)))

    record_property("mesure", f"{statuses.count(201)} réservations acceptées sur {len(statuses)}")
    assert set(statuses) == {201}


def test_pt12_mixed_workload_has_no_server_error(http, live_server, record_property):
    """25 utilisateurs simultanés enchaînent : connexion, liste des chambres, réservation, mes réservations, annulation.
    Attendu : aucune erreur serveur (5xx), toutes les étapes réussissent, durée totale < 30 s."""
    for i in range(25):
        http.post("/api/auth/register", json={"username": f"user{i}", "email": f"user{i}@example.com", "password": PASSWORD})
    with httpx.Client(base_url=live_server, timeout=30) as client:
        room_ids = [r["id"] for r in client.get("/api/rooms", headers=create_account(client, "probe").headers).json() if r["is_active"]]

    def journey(i):
        statuses = []
        with httpx.Client(base_url=live_server, timeout=30) as client:
            token = client.post("/api/auth/login", json={"email": f"user{i}@example.com", "password": PASSWORD})
            statuses.append(token.status_code)
            headers = {"Authorization": f"Bearer {token.json()['access_token']}"}
            statuses.append(client.get("/api/rooms", headers=headers).status_code)
            start, end = slot(days=2 + i // len(room_ids), hour=14, hours=1)
            booked = client.post(
                "/api/bookings",
                json={"room_id": room_ids[i % len(room_ids)], "start_at": start, "end_at": end},
                headers=headers,
            )
            statuses.append(booked.status_code)
            statuses.append(client.get("/api/bookings", headers=headers).status_code)
            statuses.append(client.delete(f"/api/bookings/{booked.json()['id']}", headers=headers).status_code)
        return statuses

    started = time.perf_counter()
    with ThreadPoolExecutor(max_workers=25) as pool:
        results = list(pool.map(journey, range(25)))
    elapsed = time.perf_counter() - started

    flat = [status for result in results for status in result]
    record_property("mesure", f"{len(flat)} requêtes en {elapsed:.2f} s, {sum(s >= 500 for s in flat)} erreur(s) 5xx")
    assert not any(status >= 500 for status in flat), flat
    assert all(result == [200, 200, 201, 200, 200] for result in results), results
    assert elapsed < 30 * FACTOR, f"{elapsed:.1f} s"
