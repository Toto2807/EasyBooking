import { useEffect, useState } from 'react';
import { api } from '../api';
import { formatDate, formatTime, toDateInput } from '../format';

// Réservation en 2 étapes : 1) choix du créneau  2) confirmation
export default function BookingModal({ room, initial, onClose, onBooked }) {
  const [date, setDate] = useState(initial.date || toDateInput(new Date()));
  const [start, setStart] = useState(initial.startTime || '09:00');
  const [end, setEnd] = useState(initial.endTime || '10:00');
  const [step, setStep] = useState('form');
  const [busy, setBusy] = useState([]);
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  // Créneaux déjà pris ce jour-là pour cette chambre
  useEffect(() => {
    if (!date) return;
    api
      .roomAvailability(room.id, date)
      .then((data) => setBusy(data.busy_slots))
      .catch(() => setBusy([]));
  }, [room.id, date]);

  function validate() {
    if (!date || !start || !end) return 'Choisissez une date, une heure de début et une heure de fin.';
    if (end <= start) return "L'heure de fin doit être après l'heure de début.";
    if (new Date(`${date}T${start}`) <= new Date()) return 'Le créneau doit commencer dans le futur.';
    return '';
  }

  function goToConfirmation(event) {
    event.preventDefault();
    const message = validate();
    setError(message);
    if (!message) setStep('confirm');
  }

  async function confirm() {
    setSubmitting(true);
    setError('');
    try {
      const booking = await api.createBooking({
        room_id: room.id,
        start_at: `${date}T${start}`,
        end_at: `${date}T${end}`,
      });
      onBooked(booking);
    } catch (err) {
      setError(err.message); // ex. « Cette chambre est déjà réservée sur ce créneau »
      setStep('form');
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="overlay" role="dialog" aria-modal="true" aria-label={`Réserver ${room.name}`}>
      <div className="card modal">
        <h2>Réserver : {room.name}</h2>
        {error && <p className="alert error">{error}</p>}

        {step === 'form' ? (
          <form className="form" onSubmit={goToConfirmation}>
            <label>
              Date
              <input type="date" min={toDateInput(new Date())} value={date} onChange={(e) => setDate(e.target.value)} />
            </label>
            <div className="row">
              <label>
                Début
                <input type="time" value={start} onChange={(e) => setStart(e.target.value)} />
              </label>
              <label>
                Fin
                <input type="time" value={end} onChange={(e) => setEnd(e.target.value)} />
              </label>
            </div>
            <p className="hint">
              {busy.length === 0
                ? 'Aucune réservation ce jour-là : toute la journée est libre.'
                : `Déjà réservé ce jour-là : ${busy.map((s) => `${formatTime(s.start_at)}–${formatTime(s.end_at)}`).join(', ')}`}
            </p>
            <div className="actions">
              <button type="button" onClick={onClose}>
                Annuler
              </button>
              <button className="primary">Continuer</button>
            </div>
          </form>
        ) : (
          <div className="form">
            <p>Confirmez-vous cette réservation ?</p>
            <ul className="summary">
              <li><strong>Chambre :</strong> {room.name} ({room.capacity} personnes)</li>
              <li><strong>Date :</strong> {formatDate(`${date}T${start}`)}</li>
              <li><strong>Créneau :</strong> {start} – {end}</li>
            </ul>
            <div className="actions">
              <button onClick={() => setStep('form')} disabled={submitting}>
                Modifier
              </button>
              <button className="primary" onClick={confirm} disabled={submitting}>
                {submitting ? 'Réservation…' : 'Confirmer la réservation'}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
