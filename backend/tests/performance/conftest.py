"""Fixtures des tests de performance : un vrai serveur HTTP (uvicorn) démarré dans le processus de test."""
import socket
import threading
import time

import httpx
import pytest
import uvicorn

from app.main import app as fastapi_app


@pytest.fixture(scope="session")
def live_server(_database):
    """Démarre l'API sur un port libre et renvoie son URL de base."""
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]

    server = uvicorn.Server(uvicorn.Config(fastapi_app, host="127.0.0.1", port=port, log_level="warning"))
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    deadline = time.time() + 20
    while not server.started and time.time() < deadline:
        time.sleep(0.05)
    assert server.started, "Le serveur de test n'a pas démarré"

    yield f"http://127.0.0.1:{port}"

    server.should_exit = True
    thread.join(timeout=10)


@pytest.fixture
def http(live_server, clean_db):
    """Client HTTP réel (httpx) vers le serveur de test, sur une base vide (chambres de départ)."""
    with httpx.Client(base_url=live_server, timeout=30) as client:
        yield client
