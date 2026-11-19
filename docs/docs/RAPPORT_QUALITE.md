# Rapport de synthèse qualité — EasyBooking

| | |
|---|---|
| **Version testée** | 1.0.0 |
| **Date d'exécution** | 19/11/2026 |
| **Environnement** | Windows 11 · Python 3.12 · PostgreSQL 16 (Docker) · FastAPI · exécution locale |
| **Documents liés** | [Plan de test](PLAN_DE_TEST.md) · [Fiche de tests](FICHE_DE_TESTS.md) · exports dans [`reports/`](reports/) |

## 1. Résumé

**Verdict : la version 1.0.0 satisfait les critères de sortie du plan de test.**

| Indicateur | Résultat | Critère |
|---|---|---|
| Cas de test | **98** (141 exécutions avec jeux de données) | ≥ 4 types × 10 cas ✅ |
| Réussite | **100 %** — 0 échec, 0 ignoré | 100 % ✅ |
| Couverture du code backend | **99 %** (398 instructions sur 401) | ≥ 80 % ✅ |
| Double réservation sous concurrence | **0** (20 requêtes simultanées → 1 réservation) | 0 ✅ |
| Erreur serveur 5xx en charge mixte | **0** sur 125 requêtes | 0 ✅ |
| Défaut applicatif ouvert | **0** | 0 ✅ |
| Durée de la suite complète | ≈ 28 s | — |

Les points d'attention (limites et risques résiduels, § 9) ne bloquent pas la livraison d'un projet pédagogique, mais doivent être traités avant une mise en production réelle.

## 2. Périmètre et méthode

- **Testé automatiquement** : l'API backend et sa base PostgreSQL (comptes, authentification, chambres, filtres, réservations, annulation, sécurité, performance).
- **Testé manuellement** : le front React (§ 7).
- **Méthode** : 4 types de tests (unitaire, intégration, sécurité, performance), chaque cas identifié et documenté dans le code ; la fiche de tests est générée depuis le code et le rapport d'exécution, ce qui garantit qu'elle correspond à ce qui a réellement été exécuté. Voir le [plan de test](PLAN_DE_TEST.md).

## 3. Résultats par type de test

| Type | Cas | Exécutions | Réussis | Échecs | Durée |
|---|---:|---:|---:|---:|---:|
| Unitaire (UT) | 26 | 45 | 26 | 0 | 0,3 s |
| Intégration (IT) | 35 | 35 | 35 | 0 | 4,1 s |
| Sécurité (ST) | 25 | 49 | 25 | 0 | 3,6 s |
| Performance (PT) | 12 | 12 | 12 | 0 | 18,8 s |
| **Total** | **98** | **141** | **98** | **0** | **26,8 s** |

Détail cas par cas : [FICHE_DE_TESTS.md](FICHE_DE_TESTS.md). Sortie brute de l'exécution : [reports/execution.txt](reports/execution.txt) ; rapport HTML : [reports/report.html](reports/report.html).

## 4. Couverture du code

| Module | Instructions | Non couvertes | Couverture |
|---|---:|---:|---:|
| `app/schemas.py` | 94 | 0 | 100 % |
| `app/routers/rooms.py` | 60 | 0 | 100 % |
| `app/main.py` | 45 | 0 | 100 % |
| `app/routers/bookings.py` | 41 | 0 | 100 % |
| `app/models.py` | 39 | 0 | 100 % |
| `app/routers/auth.py` | 35 | 3 | 91 % |
| `app/security.py` | 22 | 0 | 100 % |
| `app/deps.py` | 21 | 0 | 100 % |
| autres (`config`, `database`, `seed`, `services`) | 44 | 0 | 100 % |
| **Total** | **401** | **3** | **99 %** |

Les 3 instructions non couvertes (`auth.py`, lignes 31 à 33) correspondent au cas limite de deux inscriptions simultanées avec le même e-mail : la contrainte d'unicité de la base le bloque, mais ce chemin n'est pas rejoué par un test (voir recommandations).

## 5. Performance

Mesures relevées pendant l'exécution (serveur uvicorn réel, PostgreSQL local, requêtes HTTP). **Valeurs indicatives** : elles dépendent de la machine et varient d'une exécution à l'autre.

| Cas | Scénario | Mesure | Seuil |
|---|---|---|---|
| PT-01 | 100 × `GET /api/health` | p95 6 ms | p95 < 100 ms |
| PT-02 | 20 connexions | moyenne 8 ms | moyenne < 300 ms |
| PT-03 | Liste de 208 chambres (30 appels) | p95 19 ms | p95 < 250 ms |
| PT-04 | Recherche filtrée, 208 chambres + 300 réservations | p95 17 ms | p95 < 300 ms |
| PT-05 | 50 réservations successives | moyenne 18 ms | moyenne < 150 ms |
| PT-06 | « Mes réservations » avec 500 réservations | p95 39 ms (max 74 ms) | p95 < 400 ms |
| PT-07 | Créneaux occupés d'une chambre (100 réservations) | p95 11 ms | p95 < 200 ms |
| PT-08 | 30 inscriptions successives | moyenne 15 ms | moyenne < 300 ms |
| PT-09 | 300 requêtes par 20 utilisateurs simultanés | **91 requêtes/s**, 0 erreur | durée < 15 s |
| PT-10 | 20 réservations simultanées du même créneau | **1 acceptée, 19 refusées** | exactement 1 |
| PT-11 | 20 réservations simultanées de créneaux différents | 20 acceptées sur 20 | 20/20 |
| PT-12 | 25 parcours simultanés (connexion → réservation → annulation) | 125 requêtes en 2,7 s, **0 erreur 5xx** | 0 erreur, < 30 s |

**Lecture des résultats**

- Tous les temps de réponse sont en dessous des seuils, avec une marge d'un facteur 8 à 40 ; l'application reste fluide avec 208 chambres et 500 réservations par utilisateur.
- Les mesures varient d'une exécution à l'autre : sur nos exécutions du 19/11/2026, le p95 de PT-06 est passé de 22 ms à 108 ms sans changement de code. C'est pourquoi les seuils sont larges.
- Le point critique — **l'absence de double réservation sous concurrence** — est tenu grâce au verrouillage de la ligne de la chambre (`SELECT … FOR UPDATE`) pendant la vérification et l'insertion.
- **Réserves** : mesures sur une seule machine et un seul processus uvicorn ; le coût de bcrypt est abaissé à 4 pendant les tests (12 en production, ≈ 200 à 300 ms par connexion) ; pas de test de longue durée ni de montée en charge au-delà d'environ 25 utilisateurs simultanés.

## 6. Sécurité

Couverture par catégorie (référentiel OWASP Top 10 2021) :

| Catégorie | Cas | Résultat |
|---|---|---|
| A01 — Contrôle d'accès défaillant | ST-04 (routes protégées sans jeton), ST-16 (annulation de la réservation d'autrui), ST-17 (lecture des réservations d'autrui), ST-18 (champs `is_admin` / `user_id` imposés par le client) | ✅ Conforme : 401 sans jeton, 404 sur la ressource d'autrui, champs ignorés |
| A02 — Défaillances cryptographiques | ST-01 (mot de passe haché bcrypt), ST-02 (aucun secret dans les réponses), ST-03 (jeton sans donnée personnelle), ST-25 (clé secrète ≥ 32 caractères) | ✅ Conforme |
| A03 — Injection | ST-12 (login), ST-13 (inscription), ST-14 (filtres de chambres), ST-15 (XSS dans le nom d'utilisateur) | ✅ Conforme : requêtes paramétrées, validation stricte, aucune donnée altérée |
| A05 — Mauvaise configuration | ST-22 (CORS limité au front), ST-23 (en-têtes `nosniff`, `X-Frame-Options`, `no-store`), ST-24 (pas de trace de pile ni de détail SQL dans les erreurs) | ✅ Conforme |
| A07 — Identification et authentification | ST-05 à ST-10 (jeton mal formé, expiré, mauvaise clé, `alg: none`, utilisateur inexistant, payload modifié), ST-11 (pas d'énumération des comptes à la connexion), ST-19 (mots de passe faibles), ST-20 (mots de passe démesurés), ST-21 (le mot de passe refusé n'est pas renvoyé dans l'erreur) | ✅ Conforme |

Aucune faille exploitable n'a été trouvée par ces tests. Les risques résiduels figurent au § 9.

## 7. Vérification manuelle du front

Réalisée le 19/11/2026 dans un navigateur (serveur de développement Vite + API réelle sur PostgreSQL).

| # | Scénario | Résultat |
|---|---|---|
| M-01 | Inscription avec champs invalides (nom trop court, e-mail invalide, mot de passe faible) | ✅ Les 3 messages d'erreur s'affichent sous les champs |
| M-02 | Inscription valide | ✅ « Compte créé avec succès ! », redirection vers la connexion, e-mail pré-rempli |
| M-03 | Connexion avec mauvais mot de passe | ✅ « E-mail ou mot de passe incorrect » |
| M-04 | Connexion valide | ✅ Liste des 8 chambres, « Salle Picasso » marquée indisponible (maintenance) |
| M-05 | Filtres capacité ≥ 8 + équipement « Visioconférence » + créneau | ✅ 3 chambres attendues, badge « Libre sur ce créneau » |
| M-06 | Réservation : formulaire → récapitulatif → confirmation | ✅ Récapitulatif correct (chambre, date, créneau), réservation visible dans « Mes réservations » |
| M-07 | Réservation d'un créneau chevauchant | ✅ « Déjà réservé ce jour-là : 09:00–11:00 » affiché, puis message serveur « Cette chambre est déjà réservée sur ce créneau » |
| M-08 | Rechargement complet de la page | ✅ Session conservée |
| M-09 | Annulation d'une réservation | ✅ « Réservation annulée. », réservation déplacée dans l'historique avec le statut « Annulée » |

**Non vérifié** : déconnexion manuelle, erreur « e-mail déjà utilisé » dans l'interface, affichage mobile, captures d'écran (non disponibles lors de cette vérification). À rejouer par l'équipe avant la remise.

## 8. Anomalies et enseignements

| Réf. | Constat | Nature | Traitement |
|---|---|---|---|
| A-01 | Le premier test ST-20 attendait un code 422 à la **connexion** avec un mot de passe de 83 caractères ; l'API répond 401 (comportement correct : la connexion ne contrôle pas la force du mot de passe). | Erreur d'attendu dans le test (pas de défaut applicatif) | Test corrigé : à la connexion, 401 ou 422 sont acceptés, **jamais 500** (bcrypt est limité à 72 octets). |
| A-02 | Contrôle de sensibilité de PT-10 : le verrou `FOR UPDATE` a été retiré temporairement du code. | Vérification volontaire | Le test échoue (plusieurs réservations acceptées pour le même créneau), puis réussit après remise du verrou : **le test détecte bien une régression**. |
| A-03 | Avertissements pytest (déprécation `httpx`/Starlette, `record_property`). | Configuration des tests | `pytest.ini` ajusté (`junit_family = xunit1`, filtre ciblé). Exécution finale sans avertissement. |
| A-04 | Le rapport de couverture a montré 8 instructions jamais exécutées, dont le cas nominal de `GET /api/rooms/{id}` (seul le 404 était testé), la réponse 503 de `/api/health` et le refus de dates avec fuseau dans le filtre de chambres. | Lacune de test (pas de défaut applicatif) | Tests ajoutés : IT-34, IT-35 et IT-20 étendu. Couverture passée de 98 % à 99 %. |

**Aucun défaut applicatif n'a été détecté par la suite sur la version 1.0.0.** Plusieurs protections ont été conçues d'emblée (et sont maintenant verrouillées par des tests) : réponses 422 qui ne renvoient jamais la valeur saisie (ST-21), comparaison de hash factice quand l'e-mail est inconnu (pas d'énumération par le temps de réponse), 404 plutôt que 403 sur la réservation d'autrui, liste blanche d'algorithme JWT.

## 9. Limites et risques résiduels

| # | Risque | Gravité | Piste |
|---|---|---|---|
| R-1 | Pas de limitation des tentatives de connexion (force brute possible) | Moyenne | Limiteur de débit par IP / par compte (ex. `slowapi`), verrouillage temporaire |
| R-2 | Jeton JWT stocké dans le `localStorage` du navigateur : lisible en cas de faille XSS | Moyenne | Cookie `HttpOnly` + protection CSRF, CSP stricte |
| R-3 | La déconnexion supprime le jeton côté navigateur seulement ; il reste valide jusqu'à son expiration (60 min) | Faible | Liste de révocation ou jetons à durée courte + jeton de rafraîchissement |
| R-4 | L'inscription révèle qu'un e-mail existe déjà (demandé par l'énoncé) | Faible | Accepté volontairement ; alternative : confirmation par e-mail |
| R-5 | Pas de HTTPS en développement ; clé `SECRET_KEY` par défaut à remplacer | Haute en production | Reverse proxy TLS, variable d'environnement obligatoire |
| R-6 | Dates sans fuseau horaire (heure locale du serveur) | Faible | Stocker en UTC et convertir côté client |
| R-7 | La non-double-réservation repose sur un verrou applicatif de ligne | Faible | Ajouter une contrainte d'exclusion PostgreSQL (`btree_gist`) comme garantie au niveau de la base |
| R-8 | Pas de migrations de schéma (création des tables au démarrage) | Faible | Alembic |
| R-9 | Front non couvert par des tests automatisés ; performances mesurées sur une seule machine | Moyenne | Voir recommandations |

## 10. Recommandations

1. **Front** : ajouter des tests de composants (Vitest + Testing Library) et un parcours de bout en bout (Playwright) rejouant M-01 à M-09.
2. **Sécurité** : traiter R-1 puis R-2 en priorité avant toute mise en ligne.
3. **Base de données** : ajouter la contrainte d'exclusion (R-7) puis un test qui tente d'insérer deux réservations chevauchantes directement en SQL.
4. **Couverture** : ajouter le dernier cas limite non couvert (deux inscriptions simultanées avec le même e-mail, `auth.py` lignes 31 à 33).
5. **Intégration continue** : activer le workflow fourni (`.github/workflows/ci.yml`) pour exécuter la suite à chaque *push* et conserver les rapports en artefacts.
6. **Performance** : refaire les mesures avec `BCRYPT_ROUNDS=12`, plusieurs processus uvicorn et un outil de charge dédié (Locust ou k6) avant un dimensionnement réel.

## 11. Conclusion

La suite de 98 cas (141 exécutions) valide l'ensemble des fonctionnalités demandées, la robustesse des règles métier — en particulier l'impossibilité de réserver deux fois le même créneau, y compris sous requêtes simultanées — ainsi qu'un niveau de sécurité adapté à un projet de cette taille. La version 1.0.0 est **recommandée pour la remise**, sous réserve de rejouer les vérifications manuelles non couvertes du § 7 et de traiter les risques du § 9 avant une mise en production.

## Pour reproduire

```bash
docker compose up -d
cd backend
pip install -r requirements-dev.txt
python scripts/run_all_tests.py
```
