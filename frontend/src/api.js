// Client de l'API EasyBooking (toutes les routes commencent par /api).
const TOKEN_KEY = 'easybooking_token';
const USER_KEY = 'easybooking_user';

// Session : le jeton JWT est gardé dans le navigateur jusqu'à la déconnexion.
export const session = {
  getToken: () => localStorage.getItem(TOKEN_KEY),
  getUser() {
    try {
      return JSON.parse(localStorage.getItem(USER_KEY));
    } catch {
      return null;
    }
  },
  save(token, user) {
    localStorage.setItem(TOKEN_KEY, token);
    localStorage.setItem(USER_KEY, JSON.stringify(user));
  },
  clear() {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  },
};

export class ApiError extends Error {
  constructor(status, message) {
    super(message);
    this.status = status;
  }
}

// L'API renvoie soit un texte, soit une liste [{field, message}] (erreurs de validation).
function toMessage(detail) {
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) {
    return detail.map((e) => (e.field ? `${e.field} : ${e.message}` : e.message)).join(' • ');
  }
  return 'Une erreur est survenue';
}

async function request(path, { method = 'GET', body, params } = {}) {
  const query = new URLSearchParams();
  Object.entries(params || {}).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') query.set(key, value);
  });
  const qs = query.toString() ? `?${query}` : '';

  const headers = {};
  if (body) headers['Content-Type'] = 'application/json';
  const token = session.getToken();
  if (token) headers.Authorization = `Bearer ${token}`;

  let response;
  try {
    response = await fetch(`/api${path}${qs}`, {
      method,
      headers,
      body: body ? JSON.stringify(body) : undefined,
    });
  } catch {
    throw new ApiError(0, "Impossible de joindre le serveur. Le backend est-il démarré ?");
  }

  // Jeton refusé alors qu'on était connecté : la session a expiré.
  if (response.status === 401 && token) {
    session.clear();
    window.dispatchEvent(new Event('easybooking:session-expired'));
  }

  const data = await response.json().catch(() => null);
  if (!response.ok) throw new ApiError(response.status, toMessage(data?.detail));
  return data;
}

export const api = {
  register: (username, email, password) =>
    request('/auth/register', { method: 'POST', body: { username, email, password } }),
  login: (email, password) => request('/auth/login', { method: 'POST', body: { email, password } }),
  rooms: (filters) => request('/rooms', { params: filters }),
  roomAvailability: (roomId, date) => request(`/rooms/${roomId}/availability`, { params: { date } }),
  amenities: () => request('/rooms/amenities'),
  createBooking: (payload) => request('/bookings', { method: 'POST', body: payload }),
  myBookings: () => request('/bookings'),
  cancelBooking: (id) => request(`/bookings/${id}`, { method: 'DELETE' }),
};
