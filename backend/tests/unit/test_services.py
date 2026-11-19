"""Tests unitaires : détection de chevauchement de créneaux (app/services.py)."""
from datetime import datetime

import pytest

from app.services import intervals_overlap


def _t(hour: int, minute: int = 0) -> datetime:
    return datetime(2030, 1, 15, hour, minute)


@pytest.mark.parametrize(
    "other",
    [(_t(9), _t(11)), (_t(11), _t(13)), (_t(10, 30), _t(11, 30)), (_t(8), _t(14)), (_t(10), _t(12))],
    ids=["chevauche-debut", "chevauche-fin", "contenu", "englobant", "identique"],
)
def test_ut23_overlapping_intervals_are_detected(other):
    """Créneau 10h-12h comparé à des créneaux qui se chevauchent (début, fin, contenu, englobant, identique).
    Attendu : intervals_overlap renvoie True."""
    assert intervals_overlap(_t(10), _t(12), *other) is True


def test_ut24_back_to_back_intervals_do_not_overlap():
    """Créneaux bout à bout (10h-12h puis 12h-14h, et inversement).
    Attendu : False dans les deux sens (la fin n'est pas incluse)."""
    assert intervals_overlap(_t(10), _t(12), _t(12), _t(14)) is False
    assert intervals_overlap(_t(12), _t(14), _t(10), _t(12)) is False


def test_ut25_disjoint_intervals_do_not_overlap():
    """Créneaux séparés (10h-12h et 15h-16h).
    Attendu : intervals_overlap renvoie False."""
    assert intervals_overlap(_t(10), _t(12), _t(15), _t(16)) is False


def test_ut26_overlap_is_symmetric():
    """Le chevauchement ne dépend pas de l'ordre des arguments.
    Attendu : intervals_overlap(a, b) == intervals_overlap(b, a)."""
    a, b = (_t(10), _t(12)), (_t(11), _t(13))
    assert intervals_overlap(*a, *b) == intervals_overlap(*b, *a) is True
