import { useEffect, useState } from 'react';
import { api } from '../api';
import BookingModal from '../components/BookingModal';

const EMPTY_FILTERS = { minCapacity: '', amenity: '', date: '', startTime: '', endTime: '', availableOnly: false };

export default function RoomsPage({ onBooked }) {
  const [filters, setFilters] = useState(EMPTY_FILTERS);
  const [amenities, setAmenities] = useState([]);
  const [rooms, setRooms] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selected, setSelected] = useState(null);

  // Créneau recherché : valable seulement si date + début + fin sont renseignés et cohérents
  const { date, startTime, endTime } = filters;
  const slotStart = date && startTime && endTime && endTime > startTime ? `${date}T${startTime}` : '';
  const slotEnd = slotStart ? `${date}T${endTime}` : '';
  const slotInvalid = date && startTime && endTime && endTime <= startTime;

  useEffect(() => {
    api.amenities().then(setAmenities).catch(() => {});
  }, []);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    api
      .rooms({
        min_capacity: Number(filters.minCapacity) >= 1 ? filters.minCapacity : undefined,
        amenity: filters.amenity || undefined,
        start: slotStart || undefined,
        end: slotEnd || undefined,
        available_only: slotStart && filters.availableOnly ? 'true' : undefined,
      })
      .then((data) => {
        if (cancelled) return;
        setRooms(data);
        setError('');
      })
      .catch((err) => !cancelled && setError(err.message))
      .finally(() => !cancelled && setLoading(false));
    return () => {
      cancelled = true;
    };
  }, [filters.minCapacity, filters.amenity, filters.availableOnly, slotStart, slotEnd]);

  const setFilter = (field) => (event) =>
    setFilters({ ...filters, [field]: event.target.type === 'checkbox' ? event.target.checked : event.target.value });

  function statusLabel(room) {
    if (!room.is_active) return 'Indisponible (maintenance)';
    if (slotStart) return room.available ? 'Libre sur ce créneau' : 'Occupée sur ce créneau';
    return 'Disponible';
  }

  return (
    <>
      <h1>Chambres</h1>

      <section className="card filters">
        <label>
          Capacité minimale
          <input type="number" min="1" placeholder="ex. 6" value={filters.minCapacity} onChange={setFilter('minCapacity')} />
        </label>
        <label>
          Équipement
          <select value={filters.amenity} onChange={setFilter('amenity')}>
            <option value="">Tous</option>
            {amenities.map((name) => (
              <option key={name}>{name}</option>
            ))}
          </select>
        </label>
        <label>
          Date
          <input type="date" value={filters.date} onChange={setFilter('date')} />
        </label>
        <label>
          De
          <input type="time" value={filters.startTime} onChange={setFilter('startTime')} />
        </label>
        <label>
          À
          <input type="time" value={filters.endTime} onChange={setFilter('endTime')} />
        </label>
        <label className="check">
          <input type="checkbox" checked={filters.availableOnly} onChange={setFilter('availableOnly')} disabled={!slotStart} />
          Seulement les chambres libres
        </label>
        <button className="link" onClick={() => setFilters(EMPTY_FILTERS)}>
          Réinitialiser
        </button>
      </section>
      {slotInvalid && <p className="alert error">L'heure de fin doit être après l'heure de début.</p>}
      {!slotStart && !slotInvalid && (
        <p className="hint">Renseignez une date et une plage horaire pour voir quelles chambres sont libres.</p>
      )}

      {error && <p className="alert error">{error}</p>}
      {loading && <p className="hint">Chargement…</p>}
      {!loading && !error && rooms.length === 0 && <p className="hint">Aucune chambre ne correspond à ces filtres.</p>}

      <div className="grid">
        {rooms.map((room) => (
          <article key={room.id} className={`card room ${room.available ? '' : 'unavailable'}`}>
            <h2>{room.name}</h2>
            <p className="meta">
              {room.capacity} personnes · {room.location}
            </p>
            <p>{room.description}</p>
            <ul className="tags">
              {room.amenities.map((a) => (
                <li key={a}>{a}</li>
              ))}
            </ul>
            <div className="room-footer">
              <span className={`badge ${room.available ? 'ok' : 'ko'}`}>{statusLabel(room)}</span>
              <button className="primary" disabled={!room.available} onClick={() => setSelected(room)}>
                Réserver
              </button>
            </div>
          </article>
        ))}
      </div>

      {selected && (
        <BookingModal
          room={selected}
          initial={{ date, startTime, endTime }}
          onClose={() => setSelected(null)}
          onBooked={() => {
            setSelected(null);
            onBooked();
          }}
        />
      )}
    </>
  );
}
