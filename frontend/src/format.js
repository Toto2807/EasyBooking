const pad = (n) => String(n).padStart(2, '0');

// "2030-01-15" (format attendu par <input type="date">) pour une Date locale
export const toDateInput = (d) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;

// L'API renvoie des dates sans fuseau (heure locale) : new Date(...) les lit comme locales.
export const formatDate = (iso) =>
  new Date(iso).toLocaleDateString('fr-FR', {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  });

export const formatTime = (iso) =>
  new Date(iso).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });

export const STATUS_LABELS = { confirmed: 'Confirmée', cancelled: 'Annulée' };

// Mêmes règles que le backend (voir app/schemas.py)
export const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

// Retourne TOUTES les règles du mot de passe non respectées (tableau vide si OK),
// pour les afficher ensemble plutôt qu'une par une.
export function passwordErrors(password) {
  const errors = [];
  if (password.length < 8) errors.push('Au moins 8 caractères');
  if (!/[a-z]/.test(password)) errors.push('Ajoutez au moins une minuscule');
  if (!/[A-Z]/.test(password)) errors.push('Ajoutez au moins une majuscule');
  if (!/\d/.test(password)) errors.push('Ajoutez au moins un chiffre');
  return errors;
}

export function validateRegistration({ username, email, password }) {
  const errors = {};
  if (!/^[A-Za-z0-9_.-]{3,30}$/.test(username)) {
    errors.username = "3 à 30 caractères : lettres, chiffres, '.', '_' ou '-'";
  }
  if (!EMAIL_RE.test(email)) errors.email = "L'adresse e-mail n'est pas valide";
  const pwd = passwordErrors(password);
  if (pwd.length > 0) errors.password = pwd; // tableau : une entrée par règle manquée
  return errors;
}
