import { useEffect, useState } from 'react';
import { session } from './api';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import RoomsPage from './pages/RoomsPage';
import BookingsPage from './pages/BookingsPage';

export default function App() {
  const [user, setUser] = useState(session.getUser());
  const [page, setPage] = useState(user ? 'rooms' : 'login');
  const [notice, setNotice] = useState(null); // { type: 'success' | 'error', text }
  const [prefillEmail, setPrefillEmail] = useState('');

  // Déclenché par api.js quand le serveur refuse le jeton (session expirée)
  useEffect(() => {
    const onExpired = () => {
      setUser(null);
      setPage('login');
      setNotice({ type: 'error', text: 'Votre session a expiré, veuillez vous reconnecter.' });
    };
    window.addEventListener('easybooking:session-expired', onExpired);
    return () => window.removeEventListener('easybooking:session-expired', onExpired);
  }, []);

  const goTo = (target) => {
    setNotice(null);
    setPage(target);
  };

  const logout = () => {
    session.clear();
    setUser(null);
    setPage('login');
    setNotice({ type: 'success', text: 'Vous êtes déconnecté.' });
  };

  return (
    <>
      <header className="topbar">
        <span className="brand">EasyBooking</span>
        <nav>
          {user ? (
            <>
              <button className={page === 'rooms' ? 'active' : ''} onClick={() => goTo('rooms')}>
                Chambres
              </button>
              <button className={page === 'bookings' ? 'active' : ''} onClick={() => goTo('bookings')}>
                Mes réservations
              </button>
              <span className="who">{user.username}</span>
              <button className="link" onClick={logout}>
                Déconnexion
              </button>
            </>
          ) : (
            <>
              <button className={page === 'login' ? 'active' : ''} onClick={() => goTo('login')}>
                Connexion
              </button>
              <button className={page === 'register' ? 'active' : ''} onClick={() => goTo('register')}>
                Créer un compte
              </button>
            </>
          )}
        </nav>
      </header>

      <main className="container">
        {notice && <p className={`alert ${notice.type}`}>{notice.text}</p>}

        {!user && page === 'register' && (
          <RegisterPage
            onRegistered={(email) => {
              setPrefillEmail(email);
              setPage('login');
              setNotice({ type: 'success', text: 'Compte créé avec succès ! Vous pouvez maintenant vous connecter.' });
            }}
          />
        )}
        {!user && page !== 'register' && (
          <LoginPage
            prefillEmail={prefillEmail}
            onLoggedIn={(loggedUser) => {
              setUser(loggedUser);
              setNotice(null);
              setPage('rooms');
            }}
          />
        )}
        {user && page === 'rooms' && (
          <RoomsPage
            onBooked={() => {
              setPage('bookings');
              setNotice({ type: 'success', text: 'Réservation confirmée !' });
            }}
          />
        )}
        {user && page === 'bookings' && <BookingsPage />}
      </main>
    </>
  );
}
