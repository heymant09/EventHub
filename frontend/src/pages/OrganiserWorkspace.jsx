import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  cancelEvent,
  completeEvent,
  createEvent,
  getCategories,
  getEventRegistrations,
  getManageableEvents,
  publishEvent,
  updateEvent,
} from '../api/events'
import './OrganiserWorkspace.css'

const apiError = (error) => {
  const detail = error.response?.data?.detail
  if (Array.isArray(detail)) return detail.map((item) => item.msg).join(' ')
  return detail || 'Something went wrong. Please try again.'
}

function localDateTime(value) {
  const date = new Date(value)
  if (Number.isNaN(date.valueOf())) return ''
  return new Date(date.getTime() - date.getTimezoneOffset() * 60000).toISOString().slice(0, 16)
}

function defaultDraft() {
  const start = new Date()
  start.setDate(start.getDate() + 7)
  start.setHours(18, 0, 0, 0)
  const end = new Date(start.getTime() + 2 * 60 * 60 * 1000)
  return {
    title: '', description: '', location: '', category_ids: [], capacity: '30',
    start_time: localDateTime(start), end_time: localDateTime(end),
  }
}

function eventDraft(event) {
  return {
    title: event.title,
    description: event.description,
    location: event.location,
    category_ids: event.categories.map((category) => category.id),
    capacity: String(event.capacity),
    start_time: localDateTime(event.start_time),
    end_time: localDateTime(event.end_time),
  }
}

function EventForm({ initial, categories, busy, onSubmit, onCancel }) {
  const [draft, setDraft] = useState(() => initial ? eventDraft(initial) : defaultDraft())
  const [formError, setFormError] = useState('')

  function change(field, value) {
    setDraft((current) => ({ ...current, [field]: value }))
  }

  function toggleCategory(categoryId) {
    setDraft((current) => {
      const selected = current.category_ids.includes(categoryId)
      return {
        ...current,
        category_ids: selected
          ? current.category_ids.filter((id) => id !== categoryId)
          : [...current.category_ids, categoryId],
      }
    })
  }

  async function submit(event) {
    event.preventDefault()
    setFormError('')
    const start = new Date(draft.start_time)
    const end = new Date(draft.end_time)
    if (Number.isNaN(start.valueOf()) || Number.isNaN(end.valueOf()) || end <= start) {
      setFormError('Choose an end time later than the start time.')
      return
    }

    const payload = {
      title: draft.title.trim(),
      description: draft.description.trim(),
      location: draft.location.trim(),
      category_ids: draft.category_ids,
      capacity: Number(draft.capacity),
      start_time: start.toISOString(),
      end_time: end.toISOString(),
    }

    try {
      await onSubmit(payload)
    } catch (error) {
      setFormError(apiError(error))
    }
  }

  return <form className="organiser-event-form" onSubmit={submit}>
    <div className="organiser-form-heading">
      <div><div className="eyebrow muted">{initial ? 'UPDATE EVENT DETAILS' : 'START WITH A DRAFT'}</div><h2>{initial ? 'Edit your event' : 'Create an event'}</h2></div>
      <button className="organiser-icon-close" type="button" aria-label="Close form" onClick={onCancel}>×</button>
    </div>
    <div className="organiser-form-grid">
      <label className="organiser-field organiser-field-wide">Event title<input required minLength="3" maxLength="200" value={draft.title} onChange={(event) => change('title', event.target.value)} placeholder="e.g. Community design workshop"/></label>
      <label className="organiser-field organiser-field-wide">Description<textarea required minLength="10" rows="3" value={draft.description} onChange={(event) => change('description', event.target.value)} placeholder="Tell people what to expect"/></label>
      <label className="organiser-field">Location<input required minLength="2" maxLength="255" value={draft.location} onChange={(event) => change('location', event.target.value)} placeholder="City or venue"/></label>
      <label className="organiser-field">Capacity<input required type="number" min="1" value={draft.capacity} onChange={(event) => change('capacity', event.target.value)}/></label>
      <label className="organiser-field">Starts<input required type="datetime-local" value={draft.start_time} onChange={(event) => change('start_time', event.target.value)}/></label>
      <label className="organiser-field">Ends<input required type="datetime-local" value={draft.end_time} onChange={(event) => change('end_time', event.target.value)}/></label>
      <fieldset className="organiser-category-field organiser-field-wide"><legend>Categories</legend>{categories.length ? <div className="organiser-category-options">{categories.map((category) => <label key={category.id}><input type="checkbox" checked={draft.category_ids.includes(category.id)} onChange={() => toggleCategory(category.id)}/><span>{category.name}</span></label>)}</div> : <small>No categories are available yet. You can still save without one.</small>}</fieldset>
    </div>
    {formError && <p className="organiser-form-error" role="alert">{formError}</p>}
    <div className="organiser-form-actions"><button type="button" className="organiser-secondary-button" onClick={onCancel} disabled={busy}>Discard</button><button type="submit" className="organiser-primary-button" disabled={busy}>{busy ? 'Saving…' : initial ? 'Save changes' : 'Save draft'}</button></div>
  </form>
}

function eventDate(value) {
  const date = new Date(value)
  return Number.isNaN(date.valueOf()) ? 'Date unavailable' : date.toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' })
}

function RegistrationAttendees({ registrations }) {
  const confirmed = registrations.filter((item) => item.status === 'confirmed').length
  const waitlisted = registrations.filter((item) => item.status === 'waitlisted').length
  const cancelled = registrations.filter((item) => item.status === 'cancelled').length
  if (!registrations.length) return <div className="organiser-registration-empty">No registrations for this event yet.</div>
  return <>
    <div className="organiser-registration-summary">{registrations.length} registrations <span>·</span> {confirmed} confirmed <span>·</span> {waitlisted} waitlisted <span>·</span> {cancelled} cancelled</div>
    <div className="organiser-attendee-list">{registrations.map((registration) => <div className="organiser-attendee-row" key={registration.id}>
      <div className="organiser-attendee-avatar" aria-hidden="true">{registration.attendee?.name?.slice(0, 1).toUpperCase() || '?'}</div>
      <div className="organiser-attendee-identity"><strong>{registration.attendee?.name || `Attendee #${registration.user_id}`}</strong><span>{registration.attendee?.email || 'Email unavailable'}</span></div>
      <span className={`organiser-status status-${registration.status}`}>{registration.status}</span>
      <time>{eventDate(registration.registered_at)}</time>
    </div>)}</div>
  </>
}

function eventHasEnded(event) {
  const end = new Date(event.end_time)
  return !Number.isNaN(end.valueOf()) && end.getTime() <= Date.now()
}

export default function OrganiserWorkspace() {
  const [events, setEvents] = useState([])
  const [categories, setCategories] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [showCreate, setShowCreate] = useState(false)
  const [editingId, setEditingId] = useState(null)
  const [busyId, setBusyId] = useState(null)
  const [expandedRegistrations, setExpandedRegistrations] = useState(null)
  const [registrations, setRegistrations] = useState({})
  const [loadingRegistrations, setLoadingRegistrations] = useState(null)

  const loadEvents = useCallback(async () => {
    setError('')
    try {
      const data = await getManageableEvents()
      setEvents(data)
    } catch (err) {
      setError(apiError(err))
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    let active = true
    getCategories().then((data) => { if (active) setCategories(data) }).catch(() => { if (active) setCategories([]) })
    loadEvents()
    return () => { active = false }
  }, [loadEvents])

  async function handleCreate(payload) {
    setBusyId('new')
    try {
      const created = await createEvent(payload)
      setEvents((current) => [created, ...current])
      setShowCreate(false)
      setNotice('Draft saved. Publish it when you’re ready for people to discover it.')
    } finally {
      setBusyId(null)
    }
  }

  async function handleUpdate(payload) {
    setBusyId(editingId)
    try {
      const updated = await updateEvent(editingId, payload)
      setEvents((current) => current.map((item) => item.id === updated.id ? updated : item))
      setEditingId(null)
      setNotice('Event details updated.')
    } finally {
      setBusyId(null)
    }
  }

  async function handlePublish(event) {
    setBusyId(event.id)
    setError('')
    try {
      const updated = await publishEvent(event.id)
      setEvents((current) => current.map((item) => item.id === updated.id ? updated : item))
      setNotice('Event published and available in discovery.')
    } catch (err) {
      setError(apiError(err))
    } finally {
      setBusyId(null)
    }
  }

  async function handleCancel(event) {
    if (!window.confirm(`Cancel “${event.title}”? Attendees will no longer be able to register.`)) return
    setBusyId(event.id)
    setError('')
    try {
      const updated = await cancelEvent(event.id)
      setEvents((current) => current.map((item) => item.id === updated.id ? updated : item))
      setNotice('Event cancelled.')
    } catch (err) {
      setError(apiError(err))
    } finally {
      setBusyId(null)
    }
  }

  async function handleComplete(event) {
    if (!window.confirm(`Mark “${event.title}” as completed? Confirmed attendees will be able to leave reviews.`)) return
    setBusyId(event.id)
    setError('')
    try {
      const updated = await completeEvent(event.id)
      setEvents((current) => current.map((item) => item.id === updated.id ? updated : item))
      setNotice('Event marked completed. Confirmed attendees can now leave reviews.')
    } catch (err) {
      setError(apiError(err))
    } finally {
      setBusyId(null)
    }
  }

  async function toggleRegistrations(eventId) {
    if (expandedRegistrations === eventId) {
      setExpandedRegistrations(null)
      return
    }
    setExpandedRegistrations(eventId)
    if (registrations[eventId]) return
    setLoadingRegistrations(eventId)
    try {
      const data = await getEventRegistrations(eventId)
      setRegistrations((current) => ({ ...current, [eventId]: data }))
    } catch (err) {
      setError(apiError(err))
      setExpandedRegistrations(null)
    } finally {
      setLoadingRegistrations(null)
    }
  }

  return <main className="content organiser-workspace">
    <div className="eyebrow muted">EVENTHUB ORGANISER</div>
    <section className="organiser-heading"><div><h1>Your events,<br/><em>all in one place.</em></h1><p>Create events, keep details current, and decide when they’re ready to publish.</p></div><button className="organiser-primary-button organiser-create-button" onClick={() => { setShowCreate((visible) => !visible); setEditingId(null); setNotice('') }}>{showCreate ? 'Close form' : '+ Create event'}</button></section>

    {notice && <div className="organiser-notice" role="status">{notice}<button onClick={() => setNotice('')} aria-label="Dismiss message">×</button></div>}
    {error && <div className="organiser-alert" role="alert">{error}<button onClick={loadEvents}>Retry</button></div>}
    {showCreate && <EventForm key="new-event" categories={categories} busy={busyId === 'new'} onSubmit={handleCreate} onCancel={() => setShowCreate(false)}/>}

    <section className="organiser-events-section"><div className="organiser-section-heading"><div><div className="eyebrow muted">YOUR WORKSPACE</div><h2>Manage events <span>{events.length}</span></h2></div><button className="organiser-refresh-button" onClick={loadEvents} disabled={loading}>Refresh</button></div>
      {loading ? <div className="organiser-state">Loading your events…</div> : !events.length ? <div className="organiser-state organiser-empty"><span className="empty-spark">✳</span><div><strong>No events yet.</strong><p>Create a draft to get started. You can review it before publishing.</p><button className="organiser-text-button" onClick={() => setShowCreate(true)}>Create your first event <span>→</span></button></div></div> : <div className="organiser-event-list">{events.map((event) => <article className="organiser-event-card" key={event.id}>
        {editingId === event.id ? <EventForm key={`edit-${event.id}`} initial={event} categories={categories} busy={busyId === event.id} onSubmit={handleUpdate} onCancel={() => setEditingId(null)}/> : <>
          <div className="organiser-event-main"><div className="organiser-event-meta"><span className={`organiser-status status-${event.status}`}>{event.status}</span><span>EVENT #{event.id}</span></div><h3>{event.title}</h3><p>{event.location} <span>·</span> {eventDate(event.start_time)}</p><div className="organiser-event-categories">{event.categories?.length ? event.categories.map((category) => <span key={category.id}>{category.name}</span>) : <span>Uncategorized</span>}<span>Capacity {event.capacity}</span></div></div>
          <div className="organiser-event-actions">
            {(event.status === 'draft' || event.status === 'published') && <button className="organiser-secondary-button" onClick={() => { setEditingId(event.id); setShowCreate(false); setNotice('') }} disabled={busyId === event.id}>Edit</button>}
            {event.status === 'draft' && <button className="organiser-primary-button" onClick={() => handlePublish(event)} disabled={busyId === event.id}>{busyId === event.id ? 'Publishing…' : 'Publish'}</button>}
            {event.status === 'published' && <Link className="organiser-view-link" to={`/events/${event.id}`}>View public page ↗</Link>}
            {event.status === 'published' && eventHasEnded(event) && <button className="organiser-complete-button" onClick={() => handleComplete(event)} disabled={busyId === event.id}>{busyId === event.id ? 'Completing…' : 'Mark complete'}</button>}
            {event.status === 'published' && !eventHasEnded(event) && <span className="organiser-completion-hint">Completion available after event ends</span>}
            {(event.status === 'published' || event.status === 'completed') && <button className="organiser-secondary-button" onClick={() => toggleRegistrations(event.id)}>{expandedRegistrations === event.id ? 'Hide attendees' : 'Attendees'}</button>}
            {(event.status === 'draft' || event.status === 'published') && <button className="organiser-cancel-button" onClick={() => handleCancel(event)} disabled={busyId === event.id}>Cancel event</button>}
          </div>
          {expandedRegistrations === event.id && <div className="organiser-registration-panel">{loadingRegistrations === event.id ? <span>Loading registrations…</span> : <RegistrationAttendees registrations={registrations[event.id] || []}/>}</div>}
        </>}
      </article>)}</div>}
    </section>
    <footer className="page-footer"><span>GOOD PLANS. GOOD PEOPLE.</span><span>MADE FOR SHOWING UP <b>✦</b></span></footer>
  </main>
}
