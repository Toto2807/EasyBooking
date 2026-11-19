# Fiche de tests EasyBooking

> Fichier **généré** par `backend/scripts/generate_test_sheet.py` à partir des docstrings des tests et du rapport `docs/reports/junit.xml`. Ne pas modifier à la main : relancer `python backend/scripts/run_all_tests.py`.

- Date d'exécution : **2026-11-19 15:25:59**
- Nombre de cas de test : **98** (« jeux de données » = nombre d'exécutions pytest du cas, quand il est paramétré)

## Synthèse

| Type de test | Cas de test | Exécutions pytest | Réussis | Échecs | Durée cumulée |
|---|---:|---:|---:|---:|---:|
| Tests unitaires (UT) | 26 | 45 | 26 cas | 0 | 0.28 s |
| Tests d'intégration (IT) | 35 | 35 | 35 cas | 0 | 4.09 s |
| Tests de sécurité (ST) | 25 | 49 | 25 cas | 0 | 3.56 s |
| Tests de performance (PT) | 12 | 12 | 12 cas | 0 | 18.82 s |
| **Total** | **98** | **141** | **98 cas** | **0** | **26.75 s** |

## Tests unitaires (UT)

| ID | Cas de test | Résultat attendu | Jeux de données | Résultat | Durée |
|---|---|---|---:|---|---:|
| UT-01 | Le hash d'un mot de passe ne contient pas le mot de passe en clair. | le hash est différent du mot de passe et commence par le préfixe bcrypt '$2'. | 1 | RÉUSSI | 0.00 s |
| UT-02 | Vérification d'un mot de passe correct. | verify_password renvoie True. | 1 | RÉUSSI | 0.01 s |
| UT-03 | Vérification d'un mauvais mot de passe. | verify_password renvoie False. | 1 | RÉUSSI | 0.00 s |
| UT-04 | Deux hachages du même mot de passe. | les deux hashs sont différents (sel aléatoire) mais valident tous les deux. | 1 | RÉUSSI | 0.00 s |
| UT-05 | Vérification contre un hash mal formé (donnée corrompue en base). | renvoie False, sans lever d'exception. | 3 | RÉUSSI | 0.00 s |
| UT-06 | Création d'un jeton d'accès pour l'utilisateur 42. | le jeton décodé contient sub='42' et une date d'expiration dans le futur. | 1 | RÉUSSI | 0.00 s |
| UT-07 | Décodage d'un jeton déjà expiré. | jwt.ExpiredSignatureError. | 1 | RÉUSSI | 0.00 s |
| UT-08 | Jeton dont le contenu (sub) a été modifié sans re-signer. | jwt.InvalidSignatureError. | 1 | RÉUSSI | 0.00 s |
| UT-09 | Jeton signé avec une autre clé secrète. | jwt.InvalidSignatureError. | 1 | RÉUSSI | 0.00 s |
| UT-10 | Jeton valide mais sans date d'expiration (donc éternel). | jwt.MissingRequiredClaimError. | 1 | RÉUSSI | 0.00 s |
| UT-11 | Inscription avec des données valides (e-mail avec majuscules). | la validation passe et l'e-mail est normalisé en minuscules. | 1 | RÉUSSI | 0.00 s |
| UT-12 | Inscription avec un e-mail au mauvais format. | ValidationError. | 6 | RÉUSSI | 0.01 s |
| UT-13 | Mot de passe de 7 caractères (minimum exigé : 8). | ValidationError. | 1 | RÉUSSI | 0.00 s |
| UT-14 | Mot de passe long mais sans majuscule / sans minuscule / sans chiffre. | ValidationError. | 3 | RÉUSSI | 0.00 s |
| UT-15 | Nom d'utilisateur trop court, trop long ou avec des caractères interdits. | ValidationError. | 6 | RÉUSSI | 0.01 s |
| UT-16 | Inscription avec des champs supplémentaires non prévus (is_admin, id). | ils sont ignorés et n'apparaissent pas dans le modèle. | 1 | RÉUSSI | 0.00 s |
| UT-17 | Réservation valide (début avec des secondes). | la validation passe et les secondes sont ramenées à 0. | 1 | RÉUSSI | 0.00 s |
| UT-18 | Heure de fin égale ou antérieure à l'heure de début. | ValidationError. | 2 | RÉUSSI | 0.00 s |
| UT-19 | Réservation de 9 heures (maximum autorisé : 8 h). | ValidationError. | 1 | RÉUSSI | 0.00 s |
| UT-20 | Réservation qui commence hier. | ValidationError. | 1 | RÉUSSI | 0.00 s |
| UT-21 | Dates envoyées avec un fuseau horaire (UTC). | ValidationError (l'API n'accepte que l'heure locale sans fuseau). | 1 | RÉUSSI | 0.00 s |
| UT-22 | Réservation avec un identifiant de chambre négatif ou nul. | ValidationError. | 1 | RÉUSSI | 0.00 s |
| UT-23 | Créneau 10h-12h comparé à des créneaux qui se chevauchent (début, fin, contenu, englobant, identique). | intervals_overlap renvoie True. | 5 | RÉUSSI | 0.01 s |
| UT-24 | Créneaux bout à bout (10h-12h puis 12h-14h, et inversement). | False dans les deux sens (la fin n'est pas incluse). | 1 | RÉUSSI | 0.00 s |
| UT-25 | Créneaux séparés (10h-12h et 15h-16h). | intervals_overlap renvoie False. | 1 | RÉUSSI | 0.00 s |
| UT-26 | Le chevauchement ne dépend pas de l'ordre des arguments. | intervals_overlap(a, b) == intervals_overlap(b, a). | 1 | RÉUSSI | 0.22 s |

Code : `backend/tests/unit/test_schemas.py`, `backend/tests/unit/test_security_utils.py`, `backend/tests/unit/test_services.py`

## Tests d'intégration (IT)

| ID | Cas de test | Résultat attendu | Jeux de données | Résultat | Durée |
|---|---|---|---:|---|---:|
| IT-01 | Inscription avec des données valides. | 201, l'utilisateur est renvoyé sans mot de passe et enregistré en base. | 1 | RÉUSSI | 0.24 s |
| IT-02 | Inscription avec un e-mail déjà utilisé. | 409 avec un message explicite. | 1 | RÉUSSI | 0.08 s |
| IT-03 | Inscription avec un nom d'utilisateur déjà pris (casse différente). | 409 avec un message explicite. | 1 | RÉUSSI | 0.09 s |
| IT-04 | Inscription avec e-mail invalide, mot de passe faible et nom trop court. | 422 avec une liste d'erreurs {field, message} et aucun compte créé. | 1 | RÉUSSI | 0.05 s |
| IT-05 | Connexion avec les bons identifiants. | 200, un jeton d'accès, et ce jeton permet d'appeler une route protégée. | 1 | RÉUSSI | 0.10 s |
| IT-06 | Connexion avec un mauvais mot de passe. | 401 avec un message d'erreur. | 1 | RÉUSSI | 0.08 s |
| IT-07 | Connexion avec un e-mail inconnu. | 401 avec exactement le même message que pour un mauvais mot de passe. | 1 | RÉUSSI | 0.06 s |
| IT-08 | Connexion avec l'e-mail saisi en majuscules. | 200 (l'e-mail est normalisé). | 1 | RÉUSSI | 0.08 s |
| IT-09 | Appel de /api/auth/me avec un jeton valide. | 200 et les informations de l'utilisateur connecté. | 1 | RÉUSSI | 0.08 s |
| IT-10 | Appel de /api/auth/me sans jeton. | 401. | 1 | RÉUSSI | 0.05 s |
| IT-11 | Liste des chambres juste après installation. | 200, les 8 chambres de départ triées par nom, avec tous les champs. | 1 | RÉUSSI | 0.09 s |
| IT-12 | Filtre par capacité minimale (10 personnes). | uniquement les chambres de 10 places ou plus. | 1 | RÉUSSI | 0.09 s |
| IT-13 | Filtre par équipement « visioconférence » (en minuscules). | les chambres équipées de Visioconférence uniquement. | 1 | RÉUSSI | 0.09 s |
| IT-14 | Filtres combinés : capacité 6 à 10 et équipement « Projecteur ». | seule la Salle Cézanne correspond. | 1 | RÉUSSI | 0.08 s |
| IT-15 | Chambre en rénovation (is_active = false). | elle apparaît dans la liste mais available = false. | 1 | RÉUSSI | 0.09 s |
| IT-16 | Liste des chambres pour un créneau après une réservation de la Salle Monet. | Monet available = false sur ce créneau, true sur un autre ; available_only la masque. | 1 | RÉUSSI | 0.19 s |
| IT-17 | Liste des équipements disponibles (alimente le filtre du front). | valeurs uniques triées, contenant Wi-Fi et Projecteur. | 1 | RÉUSSI | 0.09 s |
| IT-18 | Créneaux occupés d'une chambre pour une journée donnée. | les réservations confirmées du jour, triées, sans information sur les utilisateurs. | 1 | RÉUSSI | 0.18 s |
| IT-19 | Consultation d'une chambre inexistante. | 404 pour la fiche et pour ses disponibilités. | 1 | RÉUSSI | 0.10 s |
| IT-20 | Filtre de créneau avec seulement « start », une fin avant le début, ou des dates avec fuseau horaire. | 422 dans les trois cas. | 1 | RÉUSSI | 0.10 s |
| IT-21 | Réservation d'une chambre libre sur un créneau futur. | 201, réservation « confirmed » avec le nom de la chambre et les horaires demandés. | 1 | RÉUSSI | 0.12 s |
| IT-22 | Réservation d'une chambre déjà prise sur un créneau qui chevauche. | 409 « déjà réservée » ; la première réservation reste intacte. | 1 | RÉUSSI | 0.18 s |
| IT-23 | Deux réservations bout à bout (10h-12h puis 12h-13h) sur la même chambre. | les deux sont acceptées (201). | 1 | RÉUSSI | 0.15 s |
| IT-24 | Réservation d'une chambre qui n'existe pas. | 404. | 1 | RÉUSSI | 0.08 s |
| IT-25 | Réservation de la Salle Picasso (en rénovation). | 409 « pas disponible à la réservation ». | 1 | RÉUSSI | 0.10 s |
| IT-26 | Réservation dans le passé, avec fin avant début, ou de plus de 8 h. | 422 dans les trois cas. | 1 | RÉUSSI | 0.19 s |
| IT-27 | Consultation de « mes réservations » alors que deux utilisateurs ont réservé. | chacun ne voit que les siennes, triées de la plus lointaine à la plus proche. | 1 | RÉUSSI | 0.23 s |
| IT-28 | Annulation d'une réservation puis nouvelle réservation du même créneau par un autre utilisateur. | annulation 200 (« cancelled ») puis réservation de Bob acceptée (201). | 1 | RÉUSSI | 0.18 s |
| IT-29 | Bob tente d'annuler la réservation d'Alice. | 404 et la réservation d'Alice reste confirmée. | 1 | RÉUSSI | 0.18 s |
| IT-30 | Annulation d'une réservation déjà annulée. | 409 « déjà annulée ». | 1 | RÉUSSI | 0.14 s |
| IT-31 | Annulation d'une réservation qui a déjà commencé (insérée directement en base). | 409. | 1 | RÉUSSI | 0.13 s |
| IT-32 | Annulation d'une réservation inexistante. | 404. | 1 | RÉUSSI | 0.09 s |
| IT-33 | Parcours complet : inscription → connexion → liste des chambres → réservation → mes réservations → annulation. | chaque étape réussit et l'état final montre la réservation annulée. | 1 | RÉUSSI | 0.17 s |
| IT-34 | Consultation de la fiche d'une chambre existante (Salle Cézanne). | 200 avec ses détails (capacité 10, équipements, disponible). | 1 | RÉUSSI | 0.10 s |
| IT-35 | Appel de /api/health quand la base répond, puis quand la connexion à la base échoue. | 200 {status: ok} puis 503 « Base de données indisponible » (sans détail technique). | 1 | RÉUSSI | 0.06 s |

Code : `backend/tests/integration/test_auth_api.py`, `backend/tests/integration/test_bookings_api.py`, `backend/tests/integration/test_e2e_scenario.py`, `backend/tests/integration/test_health_api.py`, `backend/tests/integration/test_rooms_api.py`

## Tests de sécurité (ST)

| ID | Cas de test | Résultat attendu | Jeux de données | Résultat | Durée |
|---|---|---|---:|---|---:|
| ST-01 | Inscription avec le mot de passe « Passw0rd! ». | en base, password_hash est un hash bcrypt et ne contient pas le mot de passe. | 1 | RÉUSSI | 0.07 s |
| ST-02 | Réponses d'inscription, de connexion et de /me. | aucune ne contient de champ ou de valeur « password » / hash bcrypt. | 1 | RÉUSSI | 0.10 s |
| ST-03 | Contenu (non signé) du jeton d'accès. | uniquement sub, iat et exp (pas d'e-mail, de mot de passe ou de rôle). | 1 | RÉUSSI | 0.07 s |
| ST-04 | Appel de chaque route protégée sans jeton. | 401 sur toutes les routes. | 8 | RÉUSSI | 0.44 s |
| ST-05 | En-tête Authorization mal formé ou jeton invalide. | 401. | 6 | RÉUSSI | 0.31 s |
| ST-06 | Jeton authentique mais expiré depuis 1 minute. | 401. | 1 | RÉUSSI | 0.08 s |
| ST-07 | Jeton forgé avec une autre clé secrète mais avec l'identifiant d'Alice. | 401. | 1 | RÉUSSI | 0.08 s |
| ST-08 | Jeton « alg: none » (sans signature) prétendant être Alice. | 401 (seul HS256 est accepté). | 1 | RÉUSSI | 0.09 s |
| ST-09 | Jeton correctement signé mais pour un utilisateur qui n'existe pas (ou plus). | 401. | 1 | RÉUSSI | 0.05 s |
| ST-10 | Alice modifie l'identifiant (sub) de son jeton pour devenir Bob, sans re-signer. | 401. | 1 | RÉUSSI | 0.12 s |
| ST-11 | Connexion avec un e-mail existant (mauvais mot de passe) puis avec un e-mail inconnu. | même code (401) et même message : impossible de deviner les comptes existants. | 1 | RÉUSSI | 0.09 s |
| ST-12 | Connexion avec une injection SQL en guise d'e-mail et de mot de passe. | 401 (jamais 200 ni 500) et la table users est intacte. | 4 | RÉUSSI | 0.32 s |
| ST-13 | Inscription avec une injection SQL dans le nom d'utilisateur et dans l'e-mail. | 422, aucun compte créé et les tables existent toujours. | 1 | RÉUSSI | 0.06 s |
| ST-14 | Filtres de chambres avec des injections SQL (équipement, capacité, date). | aucun 500, aucune fuite de données (liste vide ou 422) et les tables sont intactes. | 1 | RÉUSSI | 0.15 s |
| ST-15 | Inscription avec un nom d'utilisateur contenant du JavaScript / HTML. | 422 et rien n'est enregistré (pas de XSS stocké). | 3 | RÉUSSI | 0.16 s |
| ST-16 | Bob tente d'annuler la réservation d'Alice (accès direct par identifiant). | 404 et la réservation d'Alice reste confirmée. | 1 | RÉUSSI | 0.24 s |
| ST-17 | Bob consulte « mes réservations » alors qu'Alice en a une. | liste vide pour Bob ; la disponibilité d'une chambre n'expose pas l'identité d'Alice. | 1 | RÉUSSI | 0.18 s |
| ST-18 | Mass assignment : inscription avec is_admin/id imposés, réservation avec le user_id de Bob. | champs ignorés ; la réservation appartient à Alice (utilisateur du jeton), pas à Bob. | 1 | RÉUSSI | 0.17 s |
| ST-19 | Inscription avec un mot de passe faible (courant, sans majuscule, sans chiffre, trop court...). | 422 et aucun compte créé. | 6 | RÉUSSI | 0.33 s |
| ST-20 | Mots de passe démesurés (83 octets, 83 octets en UTF-8, 1 Mo). | 422 à l'inscription ; à la connexion 401 ou 422, jamais une erreur serveur 500 (bcrypt est limité à 72 octets : l'application doit le gérer proprement). | 3 | RÉUSSI | 0.20 s |
| ST-21 | Inscription avec un mot de passe refusé : « motdepassefaible ». | la réponse 422 ne contient pas ce mot de passe (pas de fuite dans les erreurs/journaux). | 1 | RÉUSSI | 0.05 s |
| ST-22 | Requête CORS depuis un site non autorisé puis depuis le front autorisé. | aucun en-tête Access-Control-Allow-Origin pour le site inconnu ; présent pour le front. | 1 | RÉUSSI | 0.06 s |
| ST-23 | En-têtes de sécurité HTTP sur une réponse de l'API. | nosniff, interdiction d'être affichée dans une iframe, pas de mise en cache, referrer coupé. | 1 | RÉUSSI | 0.05 s |
| ST-24 | Requêtes malformées : identifiant non numérique, route inconnue, mauvaise méthode HTTP. | 422 / 404 / 405 propres, sans trace de pile ni détail SQL ou technique dans la réponse. | 1 | RÉUSSI | 0.11 s |
| ST-25 | Clé secrète JWT utilisée par l'application. | au moins 32 caractères (une clé courte rendrait les jetons devinables par force brute). | 1 | RÉUSSI | 0.00 s |

Code : `backend/tests/security/test_security.py`

## Tests de performance (PT)

| ID | Cas de test | Résultat attendu | Jeux de données | Résultat | Durée | Mesure relevée |
|---|---|---|---:|---|---:|---|
| PT-01 | 100 appels séquentiels à /api/health (requête + connexion PostgreSQL). | tous 200 et p95 < 100 ms. | 1 | RÉUSSI | 0.84 s | p95 6 ms, moyenne 4 ms, max 10 ms (100 appels) |
| PT-02 | 20 connexions séquentielles (vérification du hash + création du jeton). | tous 200 et moyenne < 300 ms. | 1 | RÉUSSI | 0.46 s | p95 11 ms, moyenne 8 ms, max 26 ms (20 appels) |
| PT-03 | 30 listes de chambres avec 208 chambres en base. | tous 200 et p95 < 250 ms. | 1 | RÉUSSI | 0.88 s | p95 19 ms, moyenne 15 ms, max 25 ms (30 appels) |
| PT-04 | 30 recherches filtrées (capacité + équipement + créneau) avec 208 chambres et 300 réservations. | tous 200 et p95 < 300 ms. | 1 | RÉUSSI | 1.07 s | p95 17 ms, moyenne 16 ms, max 76 ms (30 appels) |
| PT-05 | 50 réservations successives (verrou de la chambre + contrôle de conflit + insertion). | toutes en 201 et moyenne < 150 ms. | 1 | RÉUSSI | 1.21 s | p95 22 ms, moyenne 18 ms, max 26 ms (50 appels) |
| PT-06 | 20 consultations de « mes réservations » alors que l'utilisateur en a 500. | 500 réservations renvoyées à chaque fois et p95 < 400 ms. | 1 | RÉUSSI | 1.06 s | p95 39 ms, moyenne 26 ms, max 74 ms (20 appels) |
| PT-07 | 30 consultations des créneaux occupés d'une chambre qui a 100 réservations (une par jour). | tous 200 et p95 < 200 ms. | 1 | RÉUSSI | 0.64 s | p95 11 ms, moyenne 9 ms, max 14 ms (30 appels) |
| PT-08 | 30 inscriptions successives (validation + hachage bcrypt + insertion). | toutes en 201 et moyenne < 300 ms. | 1 | RÉUSSI | 0.75 s | p95 20 ms, moyenne 15 ms, max 20 ms (30 appels) |
| PT-09 | 300 listes de chambres envoyées par 20 utilisateurs simultanés. | 0 erreur, durée totale < 15 s (soit plus de 20 requêtes/seconde). | 1 | RÉUSSI | 3.56 s | 300 requêtes en 3.30 s, soit 91 requêtes/s |
| PT-10 | 20 utilisateurs réservent EN MÊME TEMPS la même chambre sur le même créneau. | exactement 1 réservation acceptée (201), 19 refusées (409), aucune erreur serveur. | 1 | RÉUSSI | 2.35 s | 1 acceptée(s) (201), 19 refusée(s) (409) |
| PT-11 | 20 utilisateurs réservent EN MÊME TEMPS la même chambre sur 20 créneaux différents. | les 20 réservations sont acceptées (201), sans blocage ni erreur. | 1 | RÉUSSI | 2.45 s | 20 réservations acceptées sur 20 |
| PT-12 | 25 utilisateurs simultanés enchaînent : connexion, liste des chambres, réservation, mes réservations, annulation. | aucune erreur serveur (5xx), toutes les étapes réussissent, durée totale < 30 s. | 1 | RÉUSSI | 3.55 s | 125 requêtes en 2.65 s, 0 erreur(s) 5xx |

Code : `backend/tests/performance/test_performance.py`
