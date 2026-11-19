import { useState } from 'react';
import { api } from '../api';
import { validateRegistration } from '../format';

export default function RegisterPage({ onRegistered }) {
  const [form, setForm] = useState({ username: '', email: '', password: '' });
  const [errors, setErrors] = useState({});
  const [serverError, setServerError] = useState('');
  const [loading, setLoading] = useState(false);

  const update = (field) => (event) => setForm({ ...form, [field]: event.target.value });

  async function submit(event) {
    event.preventDefault();
    setServerError('');
    const found = validateRegistration(form);
    setErrors(found);
    if (Object.keys(found).length > 0) return;

    setLoading(true);
    try {
      await api.register(form.username.trim(), form.email.trim(), form.password);
      onRegistered(form.email.trim());
    } catch (err) {
      setServerError(err.message); // ex. « Un compte existe déjà avec cet e-mail »
    } finally {
      setLoading(false);
    }
  }

  return (
    <form className="card form" onSubmit={submit} noValidate>
      <h1>Créer un compte</h1>
      {serverError && <p className="alert error">{serverError}</p>}
      <label>
        Nom d'utilisateur
        <input value={form.username} onChange={update('username')} autoComplete="username" />
        {errors.username && <small className="field-error">{errors.username}</small>}
      </label>
      <label>
        E-mail
        <input type="email" value={form.email} onChange={update('email')} autoComplete="email" />
        {errors.email && <small className="field-error">{errors.email}</small>}
      </label>
      <label>
        Mot de passe
        <input type="password" value={form.password} onChange={update('password')} autoComplete="new-password" />
        {errors.password ? (
          <ul className="field-error-list">
            {errors.password.map((message) => (
              <li key={message} className="field-error">{message}</li>
            ))}
          </ul>
        ) : (
          <small className="hint">8 caractères minimum, avec une majuscule, une minuscule, un chiffre et un caractère spécial</small>
        )}
      </label>
      <button className="primary" disabled={loading}>
        {loading ? 'Création…' : 'Créer mon compte'}
      </button>
    </form>
  );
}
