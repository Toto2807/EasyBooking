"""Données initiales : la liste des chambres de l'établissement."""
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .models import Room

SEED_ROOMS = [
    {
        "name": "Salle Monet",
        "capacity": 4,
        "location": "Étage 1",
        "description": "Petite salle lumineuse pour les entretiens et les appels.",
        "amenities": ["Wi-Fi", "Écran"],
    },
    {
        "name": "Salle Renoir",
        "capacity": 6,
        "location": "Étage 1",
        "description": "Salle de réunion d'équipe avec tableau blanc.",
        "amenities": ["Wi-Fi", "Tableau blanc", "Écran"],
    },
    {
        "name": "Salle Degas",
        "capacity": 8,
        "location": "Étage 2",
        "description": "Salle équipée pour la visioconférence.",
        "amenities": ["Wi-Fi", "Visioconférence", "Écran", "Climatisation"],
    },
    {
        "name": "Salle Cézanne",
        "capacity": 10,
        "location": "Étage 2",
        "description": "Grande table de réunion avec vidéoprojecteur.",
        "amenities": ["Wi-Fi", "Projecteur", "Tableau blanc", "Climatisation"],
    },
    {
        "name": "Salle Manet",
        "capacity": 2,
        "location": "Rez-de-chaussée",
        "description": "Bulle de confidentialité pour deux personnes.",
        "amenities": ["Wi-Fi"],
    },
    {
        "name": "Salle Van Gogh",
        "capacity": 12,
        "location": "Étage 3",
        "description": "Salle de formation modulable.",
        "amenities": ["Wi-Fi", "Projecteur", "Visioconférence", "Tableau blanc"],
    },
    {
        "name": "Auditorium Rodin",
        "capacity": 30,
        "location": "Rez-de-chaussée",
        "description": "Auditorium pour conférences et présentations.",
        "amenities": ["Wi-Fi", "Projecteur", "Visioconférence", "Climatisation"],
    },
    {
        "name": "Salle Picasso",
        "capacity": 6,
        "location": "Étage 3",
        "description": "Salle en cours de rénovation (indisponible).",
        "amenities": ["Wi-Fi", "Écran"],
        "is_active": False,
    },
]


def seed_rooms(db: Session) -> int:
    """Insère les chambres si la table est vide. Retourne le nombre de chambres créées."""
    if db.scalar(select(func.count(Room.id))):
        return 0
    db.add_all(Room(**data) for data in SEED_ROOMS)
    db.commit()
    return len(SEED_ROOMS)
