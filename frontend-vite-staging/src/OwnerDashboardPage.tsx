import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import {
  Activity,
  Building2,
  MapPin,
  Plus,
  RefreshCw,
  Zap,
  X,
} from 'lucide-react'
import { ownerChargersApi, ownerStationsApi } from './lib/api'
import type { OwnerCharger, OwnerStation, OwnerStationCreate } from './types/api'
import './OwnerDashboardPage.css'

const initialForm: OwnerStationCreate = {
  name: '',
  location: '',
  address: '',
  connectors: ['CCS2'],
  charger_type: 'DC',
  power: 60,
  speed: 'Fast',
  available_slots: 0,
  total_slots: 1,
  price_per_kwh: 0,
  description: '',
  is_active: true,
}

export default function OwnerDashboardPage() {
  const [stations, setStations] = useState<OwnerStation[]>([])
  const [chargers, setChargers] = useState<OwnerCharger[]>([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [showForm, setShowForm] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [form, setForm] = useState<OwnerStationCreate>(initialForm)
  const [connectorText, setConnectorText] = useState('CCS2')

  async function loadDashboard() {
    setLoading(true)
    setError('')

    try {
      const stationData = await ownerStationsApi.list()
      setStations(stationData)

      try {
        const chargerData = await ownerChargersApi.list()
        setChargers(chargerData)
      } catch {
        setChargers([])
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load your stations.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void loadDashboard()
  }, [])

  function updateForm<K extends keyof OwnerStationCreate>(
    key: K,
    value: OwnerStationCreate[K],
  ) {
    setForm(current => ({ ...current, [key]: value }))
  }

  async function handleCreateStation(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError('')
    setSuccess('')

    const connectors = connectorText
      .split(',')
      .map(value => value.trim())
      .filter(Boolean)

    if (connectors.length === 0) {
      setError('Enter at least one connector type.')
      return
    }

    if (form.available_slots > form.total_slots) {
      setError('Available slots cannot exceed total slots.')
      return
    }

    setSaving(true)

    try {
      const payload = { ...form, connectors }
      await ownerStationsApi.create(payload)
      setForm(initialForm)
      setConnectorText('CCS2')
      setShowForm(false)
      setSuccess('Your charging station has been created successfully.')
      await loadDashboard()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to create the station.')
    } finally {
      setSaving(false)
    }
  }

  async function handleDeactivate(station: OwnerStation) {
    const confirmed = window.confirm(
      `Deactivate "${station.name}"? It will no longer be active.`,
    )
    if (!confirmed) return

    setError('')
    setSuccess('')

    try {
      await ownerStationsApi.deactivate(station.id)
      setSuccess(`${station.name} has been deactivated.`)
      await loadDashboard()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to deactivate station.')
    }
  }

  const activeStations = stations.filter(station => station.is_active).length

  return (
    <main className="dashboard-content owner-dashboard">
      <div className="owner-page-heading">
        <div>
          <span className="eyebrow">OWNER WORKSPACE</span>
          <h1>Station overview</h1>
          <p className="dashboard-intro">
            Manage your charging network, stations, and infrastructure.
          </p>
        </div>
        <div className="owner-heading-actions">
          <button
            className="button button-secondary button-small"
            type="button"
            onClick={() => void loadDashboard()}
            disabled={loading}
          >
            <RefreshCw size={16} /> Refresh
          </button>
          <button
            className="button button-primary button-small"
            type="button"
            onClick={() => {
              setShowForm(value => !value)
              setError('')
            }}
          >
            {showForm ? <X size={16} /> : <Plus size={16} />}
            {showForm ? 'Close form' : 'Add station'}
          </button>
        </div>
      </div>

      {error && <div className="owner-alert owner-alert-error" role="alert">{error}</div>}
      {success && <div className="owner-alert owner-alert-success" role="status">{success}</div>}

      <section className="owner-stat-grid" aria-label="Station statistics">
        <article className="owner-stat-card">
          <span className="owner-stat-icon"><Building2 size={20} /></span>
          <span className="owner-stat-label">Total stations</span>
          <strong>{loading ? '—' : stations.length}</strong>
          <small>Stations registered to you</small>
        </article>
        <article className="owner-stat-card">
          <span className="owner-stat-icon"><Activity size={20} /></span>
          <span className="owner-stat-label">Active stations</span>
          <strong>{loading ? '—' : activeStations}</strong>
          <small>Currently marked active</small>
        </article>
        <article className="owner-stat-card">
          <span className="owner-stat-icon"><Zap size={20} /></span>
          <span className="owner-stat-label">Registered chargers</span>
          <strong>{loading ? '—' : chargers.length}</strong>
          <small>Across your stations</small>
        </article>
      </section>

      {showForm && (
        <section className="owner-form-panel">
          <div className="owner-section-heading">
            <div>
              <span className="eyebrow">NEW LOCATION</span>
              <h2>Add a charging station</h2>
            </div>
          </div>

          <form className="owner-station-form" onSubmit={handleCreateStation}>
            <label>
              Station name
              <input
                required
                maxLength={255}
                value={form.name}
                onChange={event => updateForm('name', event.target.value)}
                placeholder="e.g. ChargeMate Central"
              />
            </label>
            <label>
              City / location
              <input
                required
                maxLength={255}
                value={form.location}
                onChange={event => updateForm('location', event.target.value)}
                placeholder="e.g. Vijayawada"
              />
            </label>
            <label className="owner-field-wide">
              Full address
              <input
                required
                maxLength={500}
                value={form.address}
                onChange={event => updateForm('address', event.target.value)}
                placeholder="Street, area, city, state"
              />
            </label>
            <label>
              Connector types
              <input
                required
                value={connectorText}
                onChange={event => setConnectorText(event.target.value)}
                placeholder="CCS2, Type 2"
              />
              <small>Separate multiple connectors with commas.</small>
            </label>
            <label>
              Charger type
              <select
                value={form.charger_type}
                onChange={event => updateForm('charger_type', event.target.value)}
              >
                <option value="AC">AC</option>
                <option value="DC">DC</option>
              </select>
            </label>
            <label>
              Power (kW)
              <input
                required
                type="number"
                min="0.1"
                step="0.1"
                value={form.power}
                onChange={event => updateForm('power', Number(event.target.value))}
              />
            </label>
            <label>
              Charging speed
              <select
                value={form.speed}
                onChange={event => updateForm('speed', event.target.value)}
              >
                <option value="Standard">Standard</option>
                <option value="Fast">Fast</option>
                <option value="Ultra-fast">Ultra-fast</option>
              </select>
            </label>
            <label>
              Total slots
              <input
                required
                type="number"
                min="0"
                step="1"
                value={form.total_slots}
                onChange={event => updateForm('total_slots', Number(event.target.value))}
              />
            </label>
            <label>
              Available slots
              <input
                required
                type="number"
                min="0"
                step="1"
                value={form.available_slots}
                onChange={event => updateForm('available_slots', Number(event.target.value))}
              />
            </label>
            <label>
              Price per kWh (₹)
              <input
                required
                type="number"
                min="0"
                step="0.01"
                value={form.price_per_kwh}
                onChange={event => updateForm('price_per_kwh', Number(event.target.value))}
              />
            </label>
            <label className="owner-field-wide">
              Description
              <textarea
                maxLength={1000}
                rows={3}
                value={form.description}
                onChange={event => updateForm('description', event.target.value)}
                placeholder="Describe facilities, access, and other useful details."
              />
            </label>
            <div className="owner-form-actions owner-field-wide">
              <button
                className="button button-secondary button-small"
                type="button"
                onClick={() => setShowForm(false)}
              >
                Cancel
              </button>
              <button className="button button-primary button-small" type="submit" disabled={saving}>
                {saving ? 'Creating station...' : 'Create station'}
              </button>
            </div>
          </form>
        </section>
      )}

      <section className="owner-stations-section">
        <div className="owner-section-heading">
          <div>
            <span className="eyebrow">YOUR NETWORK</span>
            <h2>My charging stations</h2>
          </div>
          <span className="owner-result-count">{stations.length} total</span>
        </div>

        {loading ? (
          <div className="owner-empty-state">
            <RefreshCw className="owner-loading-icon" size={25} />
            <strong>Loading your stations...</strong>
          </div>
        ) : stations.length === 0 ? (
          <div className="owner-empty-state">
            <span className="owner-empty-icon"><Building2 size={30} /></span>
            <h3>No stations added yet</h3>
            <p>
              Your owner workspace is ready. Add your first charging station
              to start managing your network.
            </p>
            <button
              className="button button-primary button-small"
              type="button"
              onClick={() => setShowForm(true)}
            >
              <Plus size={16} /> Add your first station
            </button>
          </div>
        ) : (
          <div className="owner-station-list">
            {stations.map(station => {
              const stationChargers = chargers.filter(
                charger => charger.station_id === station.id,
              )

              return (
                <article className="owner-station-card" key={station.id}>
                  <div className="owner-station-card-top">
                    <span className="owner-station-symbol"><Building2 size={21} /></span>
                    <span className={`owner-status ${station.is_active ? 'is-active' : 'is-inactive'}`}>
                      {station.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </div>
                  <h3>{station.name}</h3>
                  <p className="owner-station-location">
                    <MapPin size={14} /> {station.location}
                  </p>
                  <p className="owner-station-address">{station.address}</p>
                  <div className="owner-station-details">
                    <span><Zap size={14} /> {station.power} kW</span>
                    <span>{station.charger_type}</span>
                    <span>{station.available_slots}/{station.total_slots} slots</span>
                    <span>{stationChargers.length} chargers</span>
                  </div>
                  <div className="owner-station-footer">
                    <span>₹{Number(station.price_per_kwh).toFixed(2)} / kWh</span>
                    {station.is_active && (
                      <button
                        type="button"
                        className="owner-deactivate-button"
                        onClick={() => void handleDeactivate(station)}
                      >
                        Deactivate
                      </button>
                    )}
                  </div>
                </article>
              )
            })}
          </div>
        )}
      </section>
    </main>
  )
}
