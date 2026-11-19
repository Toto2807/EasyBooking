"""Configuration de l'application (lue depuis les variables d'environnement)."""
import os


def _split(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://easybooking:easybooking@localhost:5433/easybooking",
)

# En production : définir SECRET_KEY avec une longue valeur aléatoire.
SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-secret-change-me-in-production-0123456789")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

# Coût de bcrypt (12 = bon compromis en prod, 4 dans les tests pour aller vite)
BCRYPT_ROUNDS = int(os.getenv("BCRYPT_ROUNDS", "12"))

CORS_ORIGINS = _split(os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"))

# Règles métier des réservations
MAX_BOOKING_HOURS = 8
