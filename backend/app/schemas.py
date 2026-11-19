"""Schémas Pydantic : validation des entrées et forme des sorties de l'API."""
import re
from datetime import date as date_type
from datetime import datetime, timedelta

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

from . import config

USERNAME_RE = re.compile(r"^[A-Za-z0-9_.-]+$")


# ---------------------------------------------------------------- Utilisateurs
class UserCreate(BaseModel):
    # Les champs inconnus (ex. "is_admin") sont ignorés : pas de mass assignment.
    model_config = ConfigDict(extra="ignore")

    username: str = Field(min_length=3, max_length=30)
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)

    @field_validator("username")
    @classmethod
    def username_chars(cls, value: str) -> str:
        if not USERNAME_RE.match(value):
            raise ValueError(
                "Le nom d'utilisateur ne peut contenir que des lettres, chiffres, '.', '_' et '-'"
            )
        return value

    @field_validator("email")
    @classmethod
    def email_lowercase(cls, value: str) -> str:
        return value.lower()

    @field_validator("password")
    @classmethod
    def password_strength(cls, value: str) -> str:
        if len(value.encode("utf-8")) > 72:
            raise ValueError("Le mot de passe est trop long (72 octets maximum)")
        if not re.search(r"[a-z]", value):
            raise ValueError("Le mot de passe doit contenir au moins une minuscule")
        if not re.search(r"[A-Z]", value):
            raise ValueError("Le mot de passe doit contenir au moins une majuscule")
        if not re.search(r"\d", value):
            raise ValueError("Le mot de passe doit contenir au moins un chiffre")
        return value


class LoginIn(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.strip().lower()


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# --------------------------------------------------------------------- Chambres
class RoomOut(BaseModel):
    id: int
    name: str
    capacity: int
    location: str
    description: str
    amenities: list[str]
    is_active: bool
    # True si la chambre est réservable (et libre sur le créneau demandé, s'il y en a un)
    available: bool


class BusySlot(BaseModel):
    start_at: datetime
    end_at: datetime


class RoomAvailability(BaseModel):
    room_id: int
    date: date_type
    busy_slots: list[BusySlot]


# ------------------------------------------------------------------ Réservations
class BookingCreate(BaseModel):
    model_config = ConfigDict(extra="ignore")  # un "user_id" envoyé par le client est ignoré

    room_id: int = Field(gt=0)
    start_at: datetime
    end_at: datetime

    @field_validator("start_at", "end_at")
    @classmethod
    def naive_local_time(cls, value: datetime) -> datetime:
        if value.tzinfo is not None:
            raise ValueError("Les dates doivent être envoyées sans fuseau horaire (heure locale)")
        return value.replace(second=0, microsecond=0)

    @model_validator(mode="after")
    def check_slot(self):
        if self.end_at <= self.start_at:
            raise ValueError("L'heure de fin doit être après l'heure de début")
        if self.end_at - self.start_at > timedelta(hours=config.MAX_BOOKING_HOURS):
            raise ValueError(
                f"Une réservation ne peut pas dépasser {config.MAX_BOOKING_HOURS} heures"
            )
        if self.start_at <= datetime.now():
            raise ValueError("Le créneau doit commencer dans le futur")
        return self


class BookingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    room_id: int
    room_name: str
    start_at: datetime
    end_at: datetime
    status: str
    created_at: datetime
