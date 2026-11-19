"""Point d'entrée de l'API EasyBooking.

Lancer : uvicorn app.main:app --reload --port 8000
Documentation interactive : http://localhost:8000/docs
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from . import config
from .database import Base, SessionLocal, engine
from .routers import auth, bookings, rooms
from .seed import seed_rooms


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Création des tables + chambres par défaut au démarrage (pas de migrations : projet pédagogique)
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        seed_rooms(db)
    yield


app = FastAPI(
    title="EasyBooking API",
    version="1.0.0",
    description="API de réservation de chambres : comptes, chambres, réservations.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "no-referrer")
    response.headers.setdefault("Cache-Control", "no-store")
    return response


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    """Réponse 422 uniforme : [{field, message}]. On ne renvoie JAMAIS la valeur reçue
    (sinon un mot de passe refusé serait renvoyé en clair dans la réponse)."""
    errors = []
    for err in exc.errors():
        field = ".".join(str(part) for part in err["loc"] if part not in ("body", "query"))
        message = str(err["msg"]).removeprefix("Value error, ")
        errors.append({"field": field, "message": message})
    return JSONResponse(status_code=422, content={"detail": errors})


@app.get("/api/health", tags=["health"])
def health():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception:
        raise HTTPException(status_code=503, detail="Base de données indisponible")
    return {"status": "ok", "database": "ok"}


app.include_router(auth.router)
app.include_router(rooms.router)
app.include_router(bookings.router)
