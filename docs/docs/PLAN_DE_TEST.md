# Plan de test — EasyBooking

| | |
|---|---|
| **Projet** | EasyBooking — réservation de chambres |
| **Version testée** | 1.0.0 |
| **Document** | Plan de test (stratégie, périmètre, environnement, critères) |
| **Documents liés** | [Fiche de tests](FICHE_DE_TESTS.md) · [Rapport de synthèse qualité](RAPPORT_QUALITE.md) · [Documentation de l'API](API.md) |

## 1. Objectifs

1. Vérifier que l'application répond aux 5 fonctionnalités demandées : **créer un compte, se connecter, voir les chambres, réserver un créneau, gérer ses réservations**.
2. Prouver la **fiabilité des règles métier** (pas de double réservation, validation des entrées, droits d'accès).
3. Vérifier que l'API est **sécurisée** (authentification, autorisations, injections) et **assez rapide** sous charge.
4. Disposer d'une suite de tests **automatisée, rejouable en une commande** et versionnée avec le code.

## 2. Périmètre

| Dans le périmètre | Hors périmètre |
|---|---|
| API backend (FastAPI) : comptes, authentification, chambres, réservations | Tests automatisés du front React (vérifié manuellement, voir § 8) |
| Base PostgreSQL (contraintes, verrouillage, requêtes) | Tests sur navigateurs multiples / mobile |
| Sécurité applicative de l'API | Tests de pénétration de l'infrastructure, HTTPS, déploiement |
| Performance et concurrence de l'API | Tests de montée en charge à grande échelle (> quelques dizaines d'utilisateurs) |

## 3. Stratégie : 4 types de tests, au moins 10 cas chacun

| Type | Préfixe | Objectif | Niveau / technique | Dossier | Cas |
|---|---|---|---|---|---:|
| **Unitaire** | UT | Vérifier les briques isolées : hachage, jetons JWT, validation des schémas, calcul de chevauchement | Boîte blanche, sans base de données, pytest | `backend/tests/unit` | 26 |
| **Intégration** | IT | Vérifier l'API de bout en bout avec la **vraie base PostgreSQL** : inscription, connexion, chambres, réservations, parcours complet, état de santé | Boîte noire via HTTP (TestClient), base de test réelle | `backend/tests/integration` | 35 |
| **Sécurité** | ST | Vérifier l'authentification (JWT), les autorisations (IDOR), les injections SQL/XSS, l'exposition de données, CORS et en-têtes | Tests d'attaque simulés, boîte noire | `backend/tests/security` | 25 |
| **Performance** | PT | Mesurer les temps de réponse, le débit et le comportement **sous concurrence** (dont la double réservation) | Vrai serveur uvicorn + clients HTTP parallèles (httpx, threads) | `backend/tests/performance` | 12 |

Total : **98 cas de test** (141 exécutions avec les jeux de données paramétrés). Le détail de chaque cas (description, résultat attendu, résultat obtenu) est dans la [fiche de tests](FICHE_DE_TESTS.md), générée automatiquement à partir du code des tests.

### Principes

- **Un cas = une fonction de test**, identifiée `UT-xx / IT-xx / ST-xx / PT-xx`, avec dans sa docstring la description du cas et le résultat attendu (source unique de vérité pour la fiche de tests).
- **Base réelle, pas de simulation** : les tests d'intégration, sécurité et performance utilisent PostgreSQL (la base `easybooking_test`, créée automatiquement et vidée avant chaque test). Un garde-fou refuse de tourner sur une base dont le nom ne finit pas par `_test`.
- **Tests indépendants** : chaque test repart de la base vide avec les 8 chambres de départ ; aucun ordre d'exécution à respecter.
- **Données dynamiques** : les créneaux sont calculés par rapport à la date du jour (pas de date en dur qui expirerait).
- **Seuils de performance larges** (stables sur un ordinateur portable) et ajustables : `PERF_BUDGET_FACTOR=3` les triple.

## 4. Traçabilité exigences → tests

| Exigence (énoncé) | Tests |
|---|---|
| **E1 — Créer un compte** (nom, e-mail, mot de passe, validation, message succès/erreur) | UT-11 à UT-16 · IT-01 à IT-04 · ST-01, ST-13, ST-15, ST-19 à ST-21 |
| **E2 — Connexion et session** (identifiants vérifiés, erreur sinon, session maintenue) | UT-01 à UT-10 · IT-05 à IT-10 · ST-02 à ST-12 |
| **E3 — Liste des chambres** (détails, disponibilité, filtres capacité / équipement) | IT-11 à IT-20, IT-34 · ST-14 · PT-03, PT-04, PT-07 |
| **E4 — Réserver un créneau** (sélection, date/heure, vérification de disponibilité, confirmation, mise à jour) | UT-17 à UT-26 · IT-21 à IT-26 · IT-33 · PT-05, PT-10, PT-11 |
| **E5 — Mes réservations** (passées et à venir, détails, annulation) | IT-27 à IT-32 · ST-16, ST-17 · PT-06 |
| **E6 — API documentée** | [docs/API.md](API.md) + documentation interactive `/docs` (Swagger) |
| **Transverse — sécurité** | ST-18, ST-22 à ST-25 |
| **Transverse — performance / robustesse** | IT-35 (état de santé), PT-01, PT-02, PT-08, PT-09, PT-12 |

## 5. Environnement de test

| Élément | Valeur |
|---|---|
| Base de données | PostgreSQL 16 (conteneur Docker, `docker-compose.yml`), base `easybooking_test` |
| Langage / framework | Python 3.12, FastAPI, SQLAlchemy 2, Pydantic 2 |
| Outils de test | pytest, httpx, pytest-cov (couverture), pytest-html (rapport HTML), uvicorn (serveur des tests de performance) |
| Paramétrage des tests | coût bcrypt réduit à 4 (12 en production), clé JWT de test, CORS limité à `http://localhost:5173` |
| Machine de référence | Windows 11, exécution locale (processeur et réseau locaux : les performances mesurées sont indicatives) |

## 6. Données de test

- **Chambres** : les 8 chambres de départ (`app/seed.py`) — capacités de 2 à 30, équipements variés, une chambre en maintenance (« Salle Picasso »).
- **Utilisateurs** : créés par les tests via l'API (`alice`, `bob`, etc.), mot de passe conforme `Passw0rd!`.
- **Volumes (performance)** : jusqu'à 208 chambres, 500 réservations pour un utilisateur, 25 utilisateurs simultanés.
- **Données hostiles (sécurité)** : charges d'injection SQL (`' OR '1'='1`, `'; DROP TABLE users; --`), XSS (`<script>…`), jetons falsifiés (`alg: none`, mauvaise clé, payload modifié, expiré), mots de passe démesurés (1 Mo).

## 7. Critères d'entrée / de sortie

**Entrée** : base PostgreSQL démarrée (`docker compose up -d`), dépendances installées (`pip install -r requirements-dev.txt`).

**Sortie (critères d'acceptation de la version)** :

| Critère | Seuil |
|---|---|
| Cas de test exécutés | 100 % |
| Cas réussis | 100 % (aucun échec bloquant ou majeur ouvert) |
| Couverture du code backend | ≥ 80 % (mesurée : 99 %, voir rapport) |
| Au moins 4 types de tests avec ≥ 10 cas | oui |
| Double réservation sous concurrence | 0 (test PT-10) |
| Faille de sécurité connue non corrigée | 0 |

## 8. Vérification manuelle du front (non automatisée)

Le front étant volontairement simple, il a été contrôlé manuellement dans un navigateur, contre l'API réelle :

| # | Scénario | Attendu |
|---|---|---|
| M-01 | Inscription avec champs invalides | Messages d'erreur sous chaque champ, aucun appel API |
| M-02 | Inscription valide | Message de succès, redirection vers la connexion, e-mail pré-rempli |
| M-03 | Connexion avec mauvais mot de passe | Message « E-mail ou mot de passe incorrect » |
| M-04 | Connexion valide | Accès à la liste des chambres |
| M-05 | Filtres capacité + équipement + créneau | Liste réduite, badge « Libre sur ce créneau » |
| M-06 | Réservation (formulaire → confirmation → validation) | Récapitulatif correct, réservation visible dans « Mes réservations » |
| M-07 | Réservation d'un créneau déjà pris | Créneaux occupés affichés, message d'erreur du serveur |
| M-08 | Rechargement de la page | Session conservée |
| M-09 | Annulation d'une réservation | Statut « Annulée », déplacée dans l'historique |

Les résultats sont dans le [rapport de synthèse](RAPPORT_QUALITE.md#7-vérification-manuelle-du-front).

## 9. Exécution

Depuis `backend/`, avec la base démarrée :

```bash
python scripts/run_all_tests.py
```

Cette commande lance les 4 types de tests, puis produit dans `docs/reports/` : `execution.txt` (sortie console), `report.html` (rapport HTML), `junit.xml`, `coverage.xml`, et régénère `docs/FICHE_DE_TESTS.md`. Pour un seul type : `python -m pytest -m unit` (ou `integration`, `security`, `performance`).

## 10. Rôles proposés (équipe de 3)

| Rôle | Responsabilité |
|---|---|
| Membre 1 | Tests unitaires et d'intégration, backend |
| Membre 2 | Tests de sécurité, revue des failles, front |
| Membre 3 | Tests de performance, exécution finale, rapport de synthèse |

Chaque membre relit les tests des deux autres (revue croisée) avant l'exécution finale.

## 11. Risques et parades

| Risque | Parade |
|---|---|
| Tests de performance instables sur une machine lente | Seuils larges, `PERF_BUDGET_FACTOR` pour les ajuster |
| Base de test polluée ou confondue avec la base réelle | Base dédiée `_test`, garde-fou dans `conftest.py`, vidage avant chaque test |
| Tests dépendants de la date du jour | Créneaux calculés dynamiquement (`tests/helpers.py`) |
| Verrouillage / concurrence non reproductible | Barrière de synchronisation (`threading.Barrier`) pour lancer les requêtes au même instant |

## 12. Gestion des anomalies

Toute anomalie est consignée avec : identifiant du test, étape, résultat obtenu vs attendu, gravité (bloquante / majeure / mineure), correctif et test de non-régression. Aucune correction n'est livrée sans un test qui échouait avant et réussit après.
