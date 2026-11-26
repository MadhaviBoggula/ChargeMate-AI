import { useEffect, useMemo, useState } from 'react'
import {
  CalendarDays,
  Clock3,
  MapPin,
  RefreshCw,
  XCircle,
  Zap,
} from 'lucide-react'
import { Navigate } from 'react-router-dom'
import { useAuth } from './contexts/useAuth'
import { ApiError, bookingsApi, stationsApi } from './lib/api'
import type { Booking, BookingCreate, Station } from './types/api'

function localDateTimeValue(date: Date) {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')

  return `${year}-${month}-${day}T${hours}:${minutes}`
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat('en-IN', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(value))
}

function BookingsPage() {
  const { user } = useAuth()
  const [stations, setStations] = useState<Station[]>([])
  const [bookings, setBookings] = useState<Booking[]>([])
  const [stationId, setStationId] = useState('')
  const [bookingDateTime, setBookingDateTime] = useState('')
  const [duration, setDuration] = useState<30 | 60 | 120>(60)
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [cancellingId, setCancellingId] = useState<string | null>(null)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [reloadKey, setReloadKey] = useState(0)

  const minimumDateTime = useMemo(
    () => localDateTimeValue(new Date()),
    [reloadKey, loading],
  )

  useEffect(() => {
    let active = true

    async function loadData() {
      setLoading(true)
      setError('')

      try {
        const [stationResults, bookingResults] = await Promise.all([
          stationsApi.list(0, 100),
          bookingsApi.listMine(),
        ])

        if (active) {
          const activeStations = stationResults.filter(
            station => station.is_active,
          )
          setStations(activeStations)
          setBookings(bookingResults)

          if (
            !stationId ||
            !activeStations.some(station => station.id === stationId)
          ) {
            setStationId(activeStations[0]?.id ?? '')
          }
        }
      } catch (err) {
        if (active) {
          setError(
            err instanceof Error
              ? err.message
              : 'Unable to load your booking information.',
          )
        }
      } finally {
        if (active) setLoading(false)
      }
    }

    void loadData()

    return () => {
      active = false
    }
  }, [reloadKey])

  if (user?.role !== 'driver') {
    return <Navigate to="/stations" replace />
  }

  const selectedStation = stations.find(
    station => station.id === stationId,
  )

  async function handleBooking(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError('')
    setNotice('')

    if (!stationId || !bookingDateTime) {
      setError('Please select a station and booking date/time.')
      return
    }

    const selectedDate = new Date(bookingDateTime)

    if (
      Number.isNaN(selectedDate.getTime()) ||
      selectedDate.getTime() <= Date.now()
    ) {
      setError('Please choose a future date and time.')
      return
    }

    const payload: BookingCreate = {
      station_id: stationId,
      booking_time: selectedDate.toISOString(),
      duration_minutes: duration,
    }

    setSubmitting(true)

    try {
      const created = await bookingsApi.create(payload)
      setBookings(current => [created, ...current])
      setNotice('Your booking request was submitted successfully.')
      setBookingDateTime('')
      setReloadKey(value => value + 1)
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) {
        setError(
          'This time is no longer available because the station has reached its booking capacity. Please choose another time.',
        )
      } else {
        setError(
          err instanceof Error
            ? err.message
            : 'Unable to create your booking. Please try again.',
        )
      }
    } finally {
      setSubmitting(false)
    }
  }

  async function handleCancel(bookingId: string) {
    setError('')
    setNotice('')
    setCancellingId(bookingId)

    try {
      const updated = await bookingsApi.cancel(bookingId)
      setBookings(current =>
        current.map(booking =>
          booking.id === bookingId ? updated : booking,
        ),
      )
      setNotice('Your booking has been cancelled.')
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Unable to cancel this booking.',
      )
    } finally {
      setCancellingId(null)
    }
  }

  return (
    <section className="dashboard-content bookings-page">
      <div className="bookings-heading">
        <div>
          <span className="eyebrow">DRIVER WORKSPACE</span>
          <h1>Plan your next charge.</h1>
          <p className="dashboard-intro">
            Choose a charging station, reserve a time and manage your booking requests.
          </p>
        </div>
        <button
          type="button"
          className="stations-refresh"
          onClick={() => setReloadKey(value => value + 1)}
          disabled={loading}
        >
          <RefreshCw size={16} />
          Refresh
        </button>
      </div>

      {error && <div className="booking-alert booking-alert-error" role="alert">{error}</div>}
      {notice && <div className="booking-alert booking-alert-success" role="status">{notice}</div>}

      <div className="booking-layout">
        <form className="booking-form-card" onSubmit={handleBooking}>
          <div className="booking-card-heading">
            <span className="booking-icon"><CalendarDays size={21} /></span>
            <div>
              <h2>Make a reservation</h2>
              <p>Enter your preferred charging details.</p>
            </div>
          </div>

          <label htmlFor="booking-station">Charging station</label>
          <select
            id="booking-station"
            value={stationId}
            onChange={event => setStationId(event.target.value)}
            required
            disabled={loading || stations.length === 0}
          >
            <option value="">Select a station</option>
            {stations.map(station => (
              <option key={station.id} value={station.id}>
                {station.name} — {station.location || station.address || 'Location unavailable'}
              </option>
            ))}
          </select>

          {selectedStation && (
            <div className="booking-station-preview">
              <div className="booking-preview-title">
                <MapPin size={16} />
                <strong>{selectedStation.name}</strong>
              </div>
              <p>{selectedStation.location || selectedStation.address || 'Location not provided'}</p>
              <div className="booking-preview-meta">
                <span><Zap size={14} /> {selectedStation.power} kW</span>
                <span>{selectedStation.available_slots} / {selectedStation.total_slots} station slots currently listed</span>
              </div>
              <small>Station-level slot information is not a confirmation of your selected booking time.</small>
            </div>
          )}

          <label htmlFor="booking-time">Preferred date and time</label>
          <input
            id="booking-time"
            type="datetime-local"
            min={minimumDateTime}
            value={bookingDateTime}
            onChange={event => setBookingDateTime(event.target.value)}
            required
          />

          <label htmlFor="booking-duration">Charging duration</label>
          <select
            id="booking-duration"
            value={duration}
            onChange={event =>
              setDuration(Number(event.target.value) as 30 | 60 | 120)
            }
          >
            <option value={30}>30 minutes</option>
            <option value={60}>1 hour</option>
            <option value={120}>2 hours</option>
          </select>

          <div className="booking-note">
            Your requested time is checked by the server when you submit. A request is not confirmed until the server accepts it.
          </div>

          <button
            type="submit"
            className="button button-primary booking-submit"
            disabled={submitting || loading || stations.length === 0}
          >
            {submitting ? 'Submitting request...' : 'Request booking'}
            <CalendarDays size={17} />
          </button>

          {!loading && stations.length === 0 && (
            <p className="booking-empty-hint">
              No active stations are available to select right now.
            </p>
          )}
        </form>

        <aside className="booking-info-card">
          <span className="eyebrow">HOW IT WORKS</span>
          <h2>Simple, smarter charging.</h2>
          <div className="booking-step">
            <span>01</span>
            <div><strong>Choose a station</strong><p>Select an active station from the network.</p></div>
          </div>
          <div className="booking-step">
            <span>02</span>
            <div><strong>Pick your time</strong><p>Choose a future date, time and charging duration.</p></div>
          </div>
          <div className="booking-step">
            <span>03</span>
            <div><strong>Submit your request</strong><p>ChargeMate checks station capacity before creating your booking.</p></div>
          </div>
          <div className="booking-info-foot">
            <Clock3 size={17} />
            <span>Bookings are subject to server-side availability and capacity checks.</span>
          </div>
        </aside>
      </div>

      <div className="my-bookings-section">
        <div className="my-bookings-heading">
          <div>
            <span className="eyebrow">YOUR RESERVATIONS</span>
            <h2>My bookings</h2>
          </div>
          <span className="booking-count">{bookings.length} total</span>
        </div>

        {loading ? (
          <div className="booking-list-state">Loading your bookings...</div>
        ) : bookings.length === 0 ? (
          <div className="booking-list-state">
            <CalendarDays size={25} />
            <strong>No bookings yet</strong>
            <p>Your submitted booking requests will appear here.</p>
          </div>
        ) : (
          <div className="booking-list">
            {bookings.map(booking => {
              const station = stations.find(
                item => item.id === booking.station_id,
              )
              const canCancel = ['Pending', 'Approved'].includes(booking.status)

              return (
                <article className="booking-item" key={booking.id}>
                  <div className="booking-item-icon"><Zap size={20} /></div>
                  <div className="booking-item-main">
                    <strong>{station?.name ?? 'Charging station'}</strong>
                    <span>{formatDate(booking.booking_time)}</span>
                    <small>{booking.duration_minutes} minutes · Ends {formatDate(booking.end_time)}</small>
                  </div>
                  <span className={`booking-status status-${booking.status.toLowerCase()}`}>
                    {booking.status}
                  </span>
                  {canCancel && (
                    <button
                      type="button"
                      className="booking-cancel"
                      onClick={() => void handleCancel(booking.id)}
                      disabled={cancellingId === booking.id}
                    >
                      <XCircle size={15} />
                      {cancellingId === booking.id ? 'Cancelling...' : 'Cancel'}
                    </button>
                  )}
                </article>
              )
            })}
          </div>
        )}
      </div>
    </section>
  )
}

export default BookingsPage
