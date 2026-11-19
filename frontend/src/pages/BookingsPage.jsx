import { useEffect, useState } from 'react';
import { api } from '../api';
import { formatDate, formatTime, STATUS_LABELS } from '../format';

export default function BookingsPage() {
  const [bookings, setBookings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');

  async function load() {
    try {
      setBookings(await api.myBookings());
      setError('');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function cancel(booking) {
    const label = `${booking.room_name} le ${formatDate(booking.start_at)} à ${formatTime(booking.start_at)}`;
    if (!window.confirm(`Annuler la réservation : ${label} ?`)) return;
    try {
      await api.cancelBooking(booking.id);
      setMessage('Réservation annulée.');
      await load();
    } catch (err) {
      setError(err.message);
    }
  }

  const now = new Date();
  const upcoming = bookings.filter((b) => b.status === 'confirmed' && new Date(b.start_at) > now);
  const history = bookings.filter((b) => !upcoming.includes(b));
  upcoming.sort((a, b) => new Date(a.start_at) - new Date(b.start_at)); // la plus proche d'abord

  const table = (list, withCancel) => (
    <table>
      <thead>
        <tr>
          <th>Chambre</th>
          <th>Date</th>
          <th>Créneau</th>
          <th>Statut</th>
          {withCancel && <th />}
        </tr>
      </thead>
      <tbody>
        {list.map((b) => (
          <tr key={b.id}>
            <td>{b.room_name}</td>
            <td>{formatDate(b.start_at)}</td>
            <td>
              {formatTime(b.start_at)} – {formatTime(b.end_at)}
            </td>
            <td>
              <span className={`badge ${b.status === 'confirmed' ? 'ok' : 'ko'}`}>{STATUS_LABELS[b.status]}</span>
            </td>
            {withCancel && (
              <td>
                <button onClick={() => cancel(b)}>Annuler</button>
              </td>
            )}
          </tr>
        ))}
      </tbody>
    </table>
  );

  return (
    <>
      <h1>Mes réservations</h1>
      {message && <p className="alert success">{message}</p>}
      {error && <p className="alert error">{error}</p>}
      {loading && <p className="hint">Chargement…</p>}

      {!loading && bookings.length === 0 && !error && (
        <p className="hint">Vous n'avez encore aucune réservation. Rendez-vous dans « Chambres » pour en créer une.</p>
      )}

      {upcoming.length > 0 && (
        <section className="card">
          <h2>À venir</h2>
          {table(upcoming, true)}
        </section>
      )}
      {history.length > 0 && (
        <section className="card">
          <h2>Historique (passées et annulées)</h2>
          {table(history, false)}
        </section>
      )}
    </>
  );
}
