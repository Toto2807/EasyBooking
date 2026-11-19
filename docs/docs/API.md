# Documentation de l'API EasyBooking

API REST JSON (FastAPI). Documentation interactive générée automatiquement : **http://localhost:8000/docs** (Swagger) et `/redoc`.

- **URL de base** : `http://localhost:8000/api` (en développement, le front l'appelle via le proxy Vite : `/api`)
- **Authentification** : jeton JWT dans l'en-tête `Authorization: Bearer <access_token>` (obtenu à la connexion, valable 60 min)
- **Dates** : format ISO 8601 **sans fuseau horaire**, en heure locale (ex. `2026-11-25T09:00`)

## 1. Comment le front interagit avec l'API

| Écran (fichier React) | Action de l'utilisateur | Appel API |
|---|---|---|
| Inscription (`RegisterPage.jsx`) | Valide le formulaire | `POST /auth/register` |
| Connexion (`LoginPage.jsx`) | Se connecte | `POST /auth/login` → le jeton et l'utilisateur sont gardés dans le `localStorage` |
| Chambres (`RoomsPage.jsx`) | Ouvre la page / change un filtre | `GET /rooms/amenities` (une fois) puis `GET /rooms?...` à chaque changement de filtre |
| Réservation (`BookingModal.jsx`) | Choisit une date | `GET /rooms/{id}/availability?date=...` (affiche les créneaux déjà pris) |
| Réservation (`BookingModal.jsx`) | Confirme | `POST /bookings` |
| Mes réservations (`BookingsPage.jsx`) | Ouvre la page | `GET /bookings` |
| Mes réservations | Clique sur « Annuler » | `DELETE /bookings/{id}` puis `GET /bookings` |
| Déconnexion (`App.jsx`) | Clique sur « Déconnexion » | aucun appel : le jeton est supprimé du navigateur |

Principes (voir `frontend/src/api.js`) :

1. Toutes les requêtes passent par une seule fonction `request()` qui ajoute le jeton, convertit les erreurs de l'API en message lisible et lève une `ApiError`.
2. Si l'API répond **401** alors qu'un jeton était présent (session expirée), la session est effacée et l'utilisateur est renvoyé vers la connexion.
3. Le front valide les formulaires avec les **mêmes règles** que le backend (retour immédiat) ; le backend revalide toujours : il ne fait jamais confiance au client.

## 2. Format des erreurs

| Code | Signification | Corps de la réponse |
|---|---|---|
| 401 | Jeton absent, invalide ou expiré ; identifiants de connexion incorrects | `{"detail": "texte"}` |
| 404 | Ressource inconnue (ou appartenant à un autre utilisateur) | `{"detail": "texte"}` |
| 409 | Conflit métier (e-mail déjà pris, créneau déjà réservé, déjà annulée…) | `{"detail": "texte"}` |
| 422 | Données invalides | `{"detail": [{"field": "password", "message": "..."}]}` — la valeur saisie n'est jamais renvoyée |
| 503 | Base de données indisponible (`/health`) | `{"detail": "texte"}` |

## 3. Comptes et authentification

### `POST /auth/register` — créer un compte

Corps :

```json
{ "username": "alice", "email": "alice@example.com", "password": "Passw0rd!" }
```

Règles : nom d'utilisateur 3 à 30 caractères (lettres, chiffres, `.`, `_`, `-`) ; e-mail valide (enregistré en minuscules) ; mot de passe 8 à 72 octets avec au moins une minuscule, une majuscule, un chiffre et un caractère spécial (tout caractère autre qu'une lettre ou un chiffre). Les champs inconnus sont ignorés.

Réponses : **201** `{"id": 1, "username": "alice", "email": "alice@example.com"}` · **409** e-mail ou nom déjà utilisé · **422** données invalides.

### `POST /auth/login` — se connecter

Corps : `{ "email": "alice@example.com", "password": "Passw0rd!" }`

Réponses :

- **200**

  ```json
  {
    "access_token": "eyJhbGciOi...",
    "token_type": "bearer",
    "user": { "id": 1, "username": "alice", "email": "alice@example.com" }
  }
  ```

- **401** `{"detail": "E-mail ou mot de passe incorrect"}` (même message que l'e-mail soit inconnu ou le mot de passe faux)

### `GET /auth/me` — utilisateur connecté

**200** `{"id": 1, "username": "alice", "email": "alice@example.com"}` · **401** sans jeton valide.

## 4. Chambres (jeton requis)

### `GET /rooms` — liste et filtres

Paramètres de requête (tous optionnels) :

| Paramètre | Description |
|---|---|
| `min_capacity` / `max_capacity` | Capacité minimale / maximale (entiers ≥ 1) |
| `amenity` | Équipement exact, insensible à la casse (ex. `Projecteur`) |
| `start` + `end` | Créneau recherché (à fournir ensemble) : `available` tient compte des réservations |
| `available_only` | `true` : ne renvoie que les chambres libres sur le créneau |

**200** — liste triée par nom :

```json
[
  {
    "id": 4,
    "name": "Salle Cézanne",
    "capacity": 10,
    "location": "Étage 2",
    "description": "Grande table de réunion avec vidéoprojecteur.",
    "amenities": ["Wi-Fi", "Projecteur", "Tableau blanc", "Climatisation"],
    "is_active": true,
    "available": true
  }
]
```

`is_active = false` : chambre en maintenance (jamais réservable). `available` = chambre active **et** libre sur le créneau demandé (ou simplement active si aucun créneau n'est donné). **422** si `start`/`end` sont incomplets, incohérents ou avec fuseau horaire.

### `GET /rooms/amenities`

**200** `["Climatisation", "Projecteur", "Tableau blanc", "Visioconférence", "Wi-Fi", "Écran"]` (équipements existants, triés).

### `GET /rooms/{id}`

**200** la chambre (même format que ci-dessus) · **404** chambre inconnue.

### `GET /rooms/{id}/availability?date=2026-11-25`

Créneaux déjà réservés (confirmés) ce jour-là, sans information sur les utilisateurs :

```json
{ "room_id": 7, "date": "2026-11-25", "busy_slots": [ { "start_at": "2026-11-25T09:00:00", "end_at": "2026-11-25T11:00:00" } ] }
```

## 5. Réservations (jeton requis)

### `POST /bookings` — réserver

Corps : `{ "room_id": 7, "start_at": "2026-11-25T09:00", "end_at": "2026-11-25T11:00" }`

Règles : la fin est après le début ; durée maximale **8 heures** ; le créneau commence **dans le futur** ; dates sans fuseau. La réservation appartient toujours à l'utilisateur du jeton (un `user_id` envoyé est ignoré).

Réponses :

- **201**

  ```json
  {
    "id": 12, "room_id": 7, "room_name": "Auditorium Rodin",
    "start_at": "2026-11-25T09:00:00", "end_at": "2026-11-25T11:00:00",
    "status": "confirmed", "created_at": "2026-11-19T14:02:11.532"
  }
  ```

- **404** chambre inconnue · **409** « Cette chambre est déjà réservée sur ce créneau » ou chambre indisponible (maintenance) · **422** créneau invalide.

La disponibilité est vérifiée dans la même transaction que l'insertion, sous un **verrou de la ligne de la chambre** : deux demandes simultanées pour le même créneau ne peuvent pas réussir toutes les deux. Deux créneaux **bout à bout** (fin = début) sont autorisés.

### `GET /bookings` — mes réservations

**200** liste de mes réservations (passées, à venir, annulées), la plus lointaine d'abord, au même format que ci-dessus.

### `DELETE /bookings/{id}` — annuler

**200** la réservation avec `"status": "cancelled"` (le créneau redevient libre) · **404** réservation inconnue **ou appartenant à un autre utilisateur** · **409** déjà annulée, ou déjà commencée / passée.

## 6. Santé

### `GET /health`

**200** `{"status": "ok", "database": "ok"}` · **503** si la base ne répond pas. Ne nécessite pas de jeton.

## 7. Sécurité en bref

- Mots de passe hachés avec **bcrypt** ; jamais renvoyés par l'API.
- Jetons **JWT HS256** (algorithme imposé côté serveur), signés avec `SECRET_KEY`, expiration 60 min, sans donnée personnelle dans le jeton.
- Requêtes SQL **paramétrées** (SQLAlchemy) ; entrées validées (Pydantic).
- **CORS** limité aux origines de `CORS_ORIGINS` ; en-têtes `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Cache-Control: no-store`.
