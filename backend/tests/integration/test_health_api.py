"""Test d'intégration : état de santé de l'API (utilisé par la supervision)."""


def test_it35_health_reports_database_state(client, monkeypatch):
    """Appel de /api/health quand la base répond, puis quand la connexion à la base échoue.
    Attendu : 200 {status: ok} puis 503 « Base de données indisponible » (sans détail technique)."""
    ok = client.get("/api/health")
    assert ok.status_code == 200 and ok.json() == {"status": "ok", "database": "ok"}

    class BrokenEngine:
        def connect(self):
            raise RuntimeError("connexion refusée : détail interne secret")

    monkeypatch.setattr("app.main.engine", BrokenEngine())
    down = client.get("/api/health")
    assert down.status_code == 503
    assert down.json() == {"detail": "Base de données indisponible"}
    assert "secret" not in down.text
