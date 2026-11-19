# EasyBooking

Mini-application web de **réservation de chambres** : créer un compte, se connecter, consulter les chambres (avec filtres), réserver un créneau, gérer ses réservations. Le cœur du projet est sa **stratégie de tests** (unitaires, intégration, sécurité, performance).

| Couche | Technologie |
|---|---|
| Front | React 19 + Vite |
| Back | Python 3.12 · FastAPI · SQLAlchemy 2 |
| Base de données | PostgreSQL 16 (Docker) |
| Tests | pytest · httpx · pytest-cov · pytest-html |

## Structure du dépôt

```
easybooking/
├── docker-compose.yml          # PostgreSQL 16
├── backend/
│   ├── app/                    # API : main, routers/, models, schemas, security, services, seed
│   ├── tests/
│   │   ├── unit/               # tests unitaires (UT)
│   │   ├── integration/        # tests d'intégration (IT)
│   │   ├── security/           # tests de sécurité (ST)
│   │   ├── performance/        # tests de performance (PT)
│   │   ├── conftest.py         # fixtures : base de test PostgreSQL, client, comptes
│   │   └── helpers.py
│   ├── scripts/
│   │   ├── run_all_tests.py        # lance tout + exports dans docs/reports
│   │   └── generate_test_sheet.py  # génère docs/FICHE_DE_TESTS.md
│   ├── requirements.txt / requirements-dev.txt
│   └── pytest.ini
├── frontend/                   # application React (src/pages, src/components, src/api.js)
├── docs/
│   ├── PLAN_DE_TEST.md         # livrable : plan de test
│   ├── FICHE_DE_TESTS.md       # livrable : fiche de tests (générée)
│   ├── RAPPORT_QUALITE.md      # livrable : rapport de synthèse qualité
│   ├── API.md                  # documentation de l'API et de son interaction avec le front
│   └── reports/                # livrable : exports d'exécution (console, HTML, JUnit, couverture)
└── .github/workflows/ci.yml    # exécution automatique des tests
```

## Prérequis

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (pour PostgreSQL)
- Python 3.12 (ou plus récent)
- Node.js 20 ou plus récent

## Démarrage

### 1. Base de données

```bash
docker compose up -d
```

PostgreSQL écoute sur le port **5433** de la machine (utilisateur / mot de passe / base : `easybooking`). Les tables et les 8 chambres de départ sont créées automatiquement au premier lancement de l'API.

### 2. Backend (API sur http://localhost:8000)

```bash
cd backend
python -m venv .venv
```

Activer l'environnement : PowerShell `.venv\Scripts\Activate.ps1` — macOS / Linux / Git Bash `source .venv/bin/activate`. Puis :

```bash
pip install -r requirements-dev.txt
```

```bash
uvicorn app.main:app --reload --port 8000
```

Documentation interactive : http://localhost:8000/docs. Les valeurs par défaut fonctionnent avec `docker-compose.yml` ; pour les changer, voir `backend/.env.example` (variables d'environnement).

### 3. Front (http://localhost:5173)

Dans un autre terminal :

```bash
cd frontend
npm install
npm run dev
```

Le serveur Vite redirige `/api` vers `http://127.0.0.1:8000`. Créez un compte depuis l'écran « Créer un compte » : il n'y a pas de compte préexistant.

## Lancer les tests

La base PostgreSQL doit être démarrée (`docker compose up -d`). Les tests utilisent une base séparée, **`easybooking_test`**, créée et vidée automatiquement : ils ne touchent jamais à vos données de développement.

Depuis `backend/` :

```bash
python scripts/run_all_tests.py
```

Cette commande exécute les 4 types de tests, affiche le résultat dans la console et produit dans `docs/reports/` : `execution.txt`, `report.html` (à ouvrir dans un navigateur), `junit.xml`, `coverage.xml`, puis régénère `docs/FICHE_DE_TESTS.md`.

Un seul type de tests :

```bash
python -m pytest -m unit
```

Remplacer `unit` par `integration`, `security` ou `performance`. Pour un test précis : `python -m pytest -k test_pt10`.

Options utiles :

| Variable d'environnement | Effet |
|---|---|
| `PERF_BUDGET_FACTOR=3` | Multiplie les seuils de performance (machine lente) |
| `TEST_DATABASE_URL=...` | Autre base PostgreSQL de test (le nom doit finir par `_test`) |

## Livrables

| Livrable demandé | Où le trouver |
|---|---|
| Plan de test complet | [docs/PLAN_DE_TEST.md](docs/PLAN_DE_TEST.md) |
| Fiche de tests + exports d'exécution | [docs/FICHE_DE_TESTS.md](docs/FICHE_DE_TESTS.md) · [docs/reports/](docs/reports/) |
| Code des tests automatisés | [backend/tests/](backend/tests/) |
| Rapport de synthèse qualité | [docs/RAPPORT_QUALITE.md](docs/RAPPORT_QUALITE.md) |
| Documentation de l'API | [docs/API.md](docs/API.md) |

## Tests en un coup d'œil

| Type | Cas | Dossier |
|---|---:|---|
| Unitaires (UT) | 26 | `backend/tests/unit` |
| Intégration (IT) | 35 | `backend/tests/integration` |
| Sécurité (ST) | 25 | `backend/tests/security` |
| Performance (PT) | 12 | `backend/tests/performance` |
| **Total** | **98** | 141 exécutions (jeux de données paramétrés) — couverture backend 99 % |

## Règles métier

- Une réservation = une chambre + un créneau (début, fin) dans le futur, **8 heures maximum**.
- Une chambre ne peut pas être réservée deux fois sur des créneaux qui se chevauchent (même en cas de demandes simultanées) ; deux créneaux bout à bout sont acceptés.
- Une chambre en maintenance (`is_active = false`) n'est pas réservable.
- On ne peut annuler que **ses** réservations, tant qu'elles n'ont pas commencé ; l'annulation libère le créneau.

## Limites connues

Application pédagogique : pas de limitation des tentatives de connexion, jeton conservé dans le `localStorage`, pas de HTTPS ni de migrations de schéma. Le détail et les pistes d'amélioration sont dans [docs/RAPPORT_QUALITE.md](docs/RAPPORT_QUALITE.md#9-limites-et-risques-résiduels).
