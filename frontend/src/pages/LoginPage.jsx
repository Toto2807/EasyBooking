import { useState } from 'react';
import { api, session } from '../api';

export default function LoginPage({ prefillEmail, onLoggedIn }) {
  const [email, setEmail] = useState(prefillEmail || '');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  async function submit(event) {
    event.preventDefault();
    setError('');
    if (!email.trim() || !password) {
      setError("Renseignez votre e-mail et votre mot de passe.");
      return;
    }
    setLoading(true);
    try {
      const data = await api.login(email.trim(), password);
      session.save(data.access_token, data.user);
      onLoggedIn(data.user);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <form className="card form" onSubmit={submit} noValidate>
      <h1>Connexion</h1>
      {error && <p className="alert error">{error}</p>}
      <label>
        E-mail
        <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} autoComplete="email" />
      </label>
      <label>
        Mot de passe
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          autoComplete="current-password"
        />
      </label>
      <button className="primary" disabled={loading}>
        {loading ? 'Connexion…' : 'Se connecter'}
      </button>
    </form>
  );
}
