import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { cancelRegistration, getMyRegistrations } from '../api/events'
import './MyRegistrations.css'

const dateLabel = (value) => {
  const date = new Date(value)
  return Number.isNaN(date.valueOf()) ? 'Date unavailable' : date.toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' })
}

const eventDateLabel = (start, end) => {
  const startDate = new Date(start)
  const endDate = new Date(end)
  if (Number.isNaN(startDate.valueOf())) return 'Event date unavailable'
  const date = startDate.toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric', year: 'numeric' })
  const startTime = startDate.toLocaleTimeString(undefined, { hour: 'numeric', minute: '2-digit' })
  const endTime = Number.isNaN(endDate.valueOf()) ? '' : endDate.toLocaleTimeString(undefined, { hour: 'numeric', minute: '2-digit' })
  return `${date} · ${startTime}${endTime ? `–${endTime}` : ''}`
}

function errorMessage(error) {
  const detail = error.response?.data?.detail
  return Array.isArray(detail) ? detail.map((item) => item.msg).join(' ') : detail || 'Check your connection and try again.'
}

export default function MyRegistrations() {
  const [registrations, setRegistrations] = useState([])
  const [state, setState] = useState('loading')
  const [error, setError] = useState('')
  const [cancellingId, setCancellingId] = useState(null)

  const loadRegistrations = useCallback(async () => {
    try {
      const data = await getMyRegistrations()
      setRegistrations(data)
      setState(data.length ? 'success' : 'empty')
    } catch (err) {
      setError(errorMessage(err))
      setState('error')
    }
  }, [])

  useEffect(() => { loadRegistrations() }, [loadRegistrations])

  function handleRetry() {
    setState('loading')
    setError('')
    loadRegistrations()
  }

  async function handleCancel(registration) {
    setCancellingId(registration.id)
    setError('')
    try {
      const updated = await cancelRegistration(registration.event_id)
      setRegistrations((current) => current.map((item) => item.id === updated.id ? updated : item))
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setCancellingId(null)
    }
  }

  return <main className="content workspace-page">
    <div className="eyebrow muted">YOUR EVENTHUB ACCOUNT</div>
    <div className="workspace-heading"><div><h1>My <em>registrations.</em></h1><p>Keep track of the events you’ve signed up for.</p></div><Link to="/" className="hero-cta">Discover events <span>→</span></Link></div>
    {error && <div className="workspace-alert" role="alert">{error}{state === 'error' && <button onClick={handleRetry}>Try again</button>}</div>}
    {state === 'loading' && <div className="workspace-state">Loading your registrations…</div>}
    {state === 'empty' && <div className="workspace-state"><span className="empty-spark">✳</span><div><strong>No registrations yet.</strong><p>Find an event that sounds like you and save your place.</p><Link to="/" className="text-link">Explore events <span>→</span></Link></div></div>}
    {state === 'success' && <div className="registration-list">{registrations.map((registration) => <article className="registration-card" key={registration.id}>
      <div className="registration-card-symbol">✳</div><div className="registration-card-info"><div className="registration-card-top"><span>{registration.event?.status || 'EVENT'} · #{registration.event_id}</span><span className={`registration-status status-${registration.status}`}>{registration.status.replace('_', ' ')}</span></div><h2>{registration.event?.title || `Event #${registration.event_id}`}</h2><p className="registration-event-meta">{registration.event?.location || 'Location unavailable'} <span>·</span> {eventDateLabel(registration.event?.start_time, registration.event?.end_time)}</p><p>Registered {dateLabel(registration.registered_at)}</p>{['published', 'completed'].includes(registration.event?.status) && <Link to={`/events/${registration.event_id}`}>{registration.event.status === 'completed' ? 'View event & review' : 'View event'} <span>→</span></Link>}</div>
      {registration.status !== 'cancelled' && <button className="cancel-registration" onClick={() => handleCancel(registration)} disabled={cancellingId === registration.id}>{cancellingId === registration.id ? 'Cancelling…' : 'Cancel registration'}</button>}
    </article>)}</div>}
    <footer className="page-footer"><span>GOOD PLANS. GOOD PEOPLE.</span><span>MADE FOR SHOWING UP <b>✦</b></span></footer>
  </main>
}
