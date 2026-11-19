"""Fixtures partagées par tous les tests.

Les tests d'intégration / sécurité / performance utilisent une VRAIE base PostgreSQL
(`easybooking_test`, créée automatiquement). Les tests unitaires n'en ont pas besoin.

IMPORTANT : les variables d'environnement sont posées AVANT d'importer l'application.
"""
import os
import re

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import OperationalError

from tests.helpers import Account, create_account

TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+psycopg://easybooking:easybooking@localhost:5433/easybooking_test",
)
_url = make_url(TEST_DATABASE_URL)
_db_name = _url.database or ""

# Garde-fou : on vide les tables à chaque test, donc JAMAIS sur la vraie base.
if not re.fullmatch(r"[A-Za-z0-9_]+_test", _db_name):
    raise RuntimeError(
        f"TEST_DATABASE_URL doit pointer vers une base dont le nom finit par '_test' (reçu : '{_db_name}')."
    )

os.environ["DATABASE_URL"] = TEST_DATABASE_URL
os.environ["BCRYPT_ROUNDS"] = "4"  # hachage rapide pour les tests
os.environ["SECRET_KEY"] = "test-secret-key-for-pytest-only-0123456789abcdef"
os.environ["CORS_ORIGINS"] = "http://localhost:5173"

from fastapi.testclient import TestClient  # noqa: E402

from app import models  # noqa: E402,F401  (enregistre les tables)
from app.database import Base, SessionLocal, engine  # noqa: E402
from app.main import app as fastapi_app  # noqa: E402
from app.seed import seed_rooms  # noqa: E402


def pytest_collection_modifyitems(items):
    """Pose automatiquement le marqueur (unit/integration/performance/security) selon le dossier."""
    for item in items:
        for kind in ("unit", "integration", "performance", "security"):
            if kind in item.path.parts:
                item.add_marker(getattr(pytest.mark, kind))


def _ensure_test_database() -> None:
    admin = create_engine(_url.set(database="postgres"), isolation_level="AUTOCOMMIT")
    try:
        with admin.connect() as conn:
            exists = conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :name"), {"name": _db_name}
            ).first()
            if not exists:
                conn.execute(text(f'CREATE DATABASE "{_db_name}"'))
    finally:
        admin.dispose()


@pytest.fixture(scope="session")
def _database():
    """Prépare la base de test : création si besoin, puis tables neuves."""
    try:
        _ensure_test_database()
    except OperationalError as exc:
        pytest.fail(
            "PostgreSQL est injoignable. Lancez d'abord la base : `docker compose up -d` "
            f"(à la racine du projet).\nDétail : {exc.orig}",
            pytrace=False,
        )
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield
    engine.dispose()


@pytest.fixture
def clean_db(_database):
    """Vide toutes les tables puis réinsère les chambres de départ."""
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE bookings, users, rooms RESTART IDENTITY CASCADE"))
    with SessionLocal() as db:
        seed_rooms(db)


@pytest.fixture
def client(clean_db):
    """Client HTTP en mémoire (TestClient) branché sur la base de test."""
    return TestClient(fastapi_app)


@pytest.fixture
def db_session(clean_db):
    with SessionLocal() as db:
        yield db


@pytest.fixture
def alice(client) -> Account:
    return create_account(client, "alice")


@pytest.fixture
def bob(client) -> Account:
    return create_account(client, "bob")
