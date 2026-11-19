"""Fonctions utilitaires partagées par les tests."""
from dataclasses import dataclass
from datetime import datetime, timedelta

PASSWORD = "Passw0rd!"


def slot(days: int = 7, hour: int = 10, hours: int = 2) -> tuple[str, str]:
    """Créneau dans le futur : (début, fin) au format ISO 8601, heure locale, sans fuseau."""
    start = (datetime.now() + timedelta(days=days)).replace(hour=hour, minute=0, second=0, microsecond=0)
    end = start + timedelta(hours=hours)
    return start.isoformat(), end.isoformat()


@dataclass
class Account:
    id: int
    username: str
    email: str
    password: str
    token: str

    @property
    def headers(self) -> dict:
        return {"Authorization": f"Bearer {self.token}"}


def register(client, username: str = "alice", email: str | None = None, password: str = PASSWORD):
    return client.post(
        "/api/auth/register",
        json={"username": username, "email": email or f"{username}@example.com", "password": password},
    )


def login(client, email: str, password: str = PASSWORD):
    return client.post("/api/auth/login", json={"email": email, "password": password})


def create_account(client, username: str = "alice") -> Account:
    """Inscrit puis connecte un utilisateur (via l'API) et retourne ses identifiants + son jeton."""
    email = f"{username}@example.com"
    response = register(client, username, email)
    assert response.status_code == 201, response.text
    user_id = response.json()["id"]
    response = login(client, email)
    assert response.status_code == 200, response.text
    return Account(user_id, username, email, PASSWORD, response.json()["access_token"])


def room_id_by_name(client, headers: dict, name: str) -> int:
    rooms = client.get("/api/rooms", headers=headers).json()
    return next(room["id"] for room in rooms if room["name"] == name)


def book(client, account: Account, room_id: int, start: str, end: str):
    return client.post(
        "/api/bookings",
        json={"room_id": room_id, "start_at": start, "end_at": end},
        headers=account.headers,
    )
