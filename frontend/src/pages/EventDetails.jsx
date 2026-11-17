import { useEffect, useState } from 'react'
import { Link, useLocation, useParams } from 'react-router-dom'
import { createEventReview, deleteEventReview, getEvent, getEventReviews, getMyRegistrations, registerForEvent, updateEventReview } from '../api/events'
import { useContext } from 'react'
import { AuthContext } from '../context/AuthContext'
import './EventDetails.css'
import './EventDetailsRegistration.css'

const formatDate = (value, options) => {
  const date = new Date(value)
  return Number.isNaN(date.valueOf()) ? 'To be announced' : date.toLocaleString(undefined, options)
}

function Reviews({ reviews, summary, ownReview, onEdit }) {
  return <section className="detail-reviews"><div className="detail-section-heading"><div><div className="eyebrow muted">FROM THE COMMUNITY</div><h2>Reviews <em>& notes.</em></h2></div><div className="rating-summary"><strong>{summary?.average_rating == null ? '—' : Number(summary.average_rating).toFixed(1)}</strong><span>★</span><small>{summary?.total_reviews ?? 0} reviews</small></div></div>
    {reviews.length ? <div className="review-list">{reviews.map((review) => <article className="review-card" key={review.id}><div className="review-top"><b>{review.author?.name || 'Event attendee'}</b><span>{'★'.repeat(review.rating)}<i>{'☆'.repeat(5 - review.rating)}</i></span></div><small>{formatDate(review.updated_at || review.created_at, { dateStyle: 'medium' })}{review.updated_at !== review.created_at && ' · edited'}</small>{review.comment && <p>{review.comment}</p>}{ownReview?.id === review.id && <button type="button" className="review-edit-link" onClick={() => onEdit(review)}>Edit your review</button>}</article>)}</div> : <div className="review-empty">No reviews yet. Be the first to share your experience after the event.</div>}
  </section>
}

function ReviewComposer({ eventId, existingReview, onCreated, onUpdated, onDeleted, onCancel }) {
  const [rating, setRating] = useState(existingReview?.rating || 5)
  const [comment, setComment] = useState(existingReview?.comment || '')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)

  async function submit(event) {
    event.preventDefault()
    setSubmitting(true)
    setError('')
    try {
      const payload = { rating, comment: comment.trim() || null }
      if (existingReview) await onUpdated(await updateEventReview(eventId, existingReview.id, payload))
      else {
        const review = await createEventReview(eventId, payload)
        await onCreated(review)
        setSuccess(true)
        setComment('')
      }
    } catch (err) {
      const detail = err.response?.data?.detail
      setError(Array.isArray(detail) ? detail.map((item) => item.msg).join(' ') : detail || 'Your review could not be submitted. Please try again.')
    } finally {
      setSubmitting(false)
    }
  }

  async function removeReview() {
    if (!window.confirm('Delete your review? This cannot be undone.')) return
    setSubmitting(true)
    setError('')
    try { await deleteEventReview(eventId, existingReview.id); await onDeleted(existingReview.id) }
    catch (err) {
      const detail = err.response?.data?.detail
      setError(Array.isArray(detail) ? detail.map((item) => item.msg).join(' ') : detail || 'Your review could not be deleted. Please try again.')
    } finally { setSubmitting(false) }
  }

  return <form className="review-composer" onSubmit={submit}>
    <div className="eyebrow muted">YOU WERE THERE</div>
    <h3>{existingReview ? 'Edit your review' : 'Share your experience'}</h3>
    <label className="review-rating-label">Your rating</label>
    <div className="review-rating-picker" role="group" aria-label="Choose a rating from one to five stars">{[1, 2, 3, 4, 5].map((value) => <button key={value} type="button" aria-label={`${value} star${value === 1 ? '' : 's'}`} aria-pressed={rating === value} onClick={() => setRating(value)}>{value <= rating ? '★' : '☆'}</button>)}</div>
    <label className="review-comment-label">A note about the event<textarea rows="3" maxLength="2000" value={comment} onChange={(event) => setComment(event.target.value)} placeholder="What stood out to you?"/></label>
    <div className="review-form-footer"><small>{comment.length}/2000</small><div className="review-editor-actions">{existingReview && <><button type="button" className="review-delete" onClick={removeReview} disabled={submitting}>Delete</button><button type="button" className="review-cancel" onClick={onCancel} disabled={submitting}>Discard</button></>}<button type="submit" className="review-submit" disabled={submitting}>{submitting ? 'Saving…' : existingReview ? 'Save changes' : 'Submit review'}</button></div></div>
    {error && <p className="review-form-error" role="alert">{error}</p>}
    {success && <p className="review-form-success" role="status">Thanks for sharing your experience.</p>}
  </form>
}

export default function EventDetails() {
  const { eventId } = useParams()
  const location = useLocation()
  const { token, user } = useContext(AuthContext)
  const [event, setEvent] = useState(null)
  const [reviews, setReviews] = useState([])
  const [summary, setSummary] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [registration, setRegistration] = useState(null)
  const [registrationLoading, setRegistrationLoading] = useState(Boolean(token))
  const [registering, setRegistering] = useState(false)
  const [registerError, setRegisterError] = useState('')
  const [editingReview, setEditingReview] = useState(null)

  useEffect(() => {
    let active = true
    setLoading(true); setError('')
    Promise.all([getEvent(eventId), getEventReviews(eventId)])
      .then(([eventData, reviewData]) => {
        if (!active) return
        setEvent(eventData); setReviews(reviewData.reviews); setSummary(reviewData.summary)
      })
      .catch((err) => { if (active) setError(err.response?.data?.detail || 'Unable to load this event. Please try again.') })
      .finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [eventId])

  useEffect(() => {
    let active = true
    if (!token) {
      setRegistration(null)
      setRegistrationLoading(false)
      return () => { active = false }
    }

    setRegistrationLoading(true)
    getMyRegistrations()
      .then((registrations) => {
        if (!active) return
        const current = registrations.find((item) => String(item.event_id) === String(eventId) && item.status !== 'cancelled')
        setRegistration(current || null)
      })
      .catch(() => { if (active) setRegistration(null) })
      .finally(() => { if (active) setRegistrationLoading(false) })

    return () => { active = false }
  }, [eventId, token])

  async function handleRegister() {
    if (registering || registration) return
    setRegistering(true); setRegisterError('')
    try { setRegistration(await registerForEvent(eventId)) }
    catch (err) { setRegisterError(err.response?.data?.detail || 'Registration failed. Please try again.') }
    finally { setRegistering(false) }
  }

  async function handleReviewCreated(review) {
    setReviews((current) => [review, ...current.filter((item) => item.id !== review.id)])
    try {
      const updated = await getEventReviews(eventId)
      setReviews(updated.reviews)
      setSummary(updated.summary)
    } catch {
      // The submitted review is already shown; the existing rating summary stays visible.
    }
  }

  async function refreshReviewSummary() {
    try {
      const updated = await getEventReviews(eventId)
      setSummary(updated.summary)
      return updated.reviews
    } catch { return null }
  }

  async function handleReviewUpdated(review) {
    setReviews((current) => [review, ...current.filter((item) => item.id !== review.id)])
    const refreshed = await refreshReviewSummary()
    if (refreshed) setReviews(refreshed.some((item) => item.id === review.id) ? refreshed : [review, ...refreshed.filter((item) => item.id !== review.id)])
    setEditingReview(null)
  }

  async function handleReviewDeleted(reviewId) {
    setReviews((current) => current.filter((item) => item.id !== reviewId))
    const refreshed = await refreshReviewSummary()
    if (refreshed) setReviews(refreshed)
    setEditingReview(null)
  }

  if (loading) return <main className="content detail-loading"><div className="event-skeleton"/><div className="event-skeleton"/></main>
  if (error) return <main className="content detail-error"><div className="eyebrow muted">EVENT DETAILS</div><h1>We couldn’t open this event.</h1><p>{error}</p><Link to="/" className="hero-cta">Back to discovery <span>→</span></Link></main>
  if (!event) return null

  const start = new Date(event.start_time)
  const end = new Date(event.end_time)
  const statusText = registration?.status
  const ownReview = reviews.find((review) => review.author?.id === user?.id)
  const canReview = event.status === 'completed'
    && user?.role === 'attendee'
    && registration?.status === 'confirmed'

  return <main className="content event-details">
    <Link to="/" className="back-link">← Back to discovery</Link>
    <section className="detail-hero"><div className="detail-cover"><div className="detail-cover-top">EVENTHUB&nbsp; / &nbsp;GATHER TOGETHER <span>{event.status}</span></div><div className="detail-cover-symbol">✳</div><div className="detail-cover-bottom"><span>MAKE TIME FOR</span><b>something memorable.</b></div></div><div className="detail-title"><div className="eyebrow"><span/> EVENT DISCOVERY</div><h1>{event.title}</h1><div className="detail-meta"><span>⌖ &nbsp;{event.location}</span><span>◷ &nbsp;{formatDate(event.start_time, { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' })}</span><span>◴ &nbsp;{Number.isNaN(start.valueOf()) ? 'Time TBA' : start.toLocaleTimeString(undefined, { hour: 'numeric', minute: '2-digit' })}{!Number.isNaN(end.valueOf()) && ` – ${end.toLocaleTimeString(undefined, { hour: 'numeric', minute: '2-digit' })}`}</span></div><div className="detail-categories">{event.categories?.length ? event.categories.map((category) => <span key={category.id}>{category.name}</span>) : <span>Community event</span>}</div></div></section>
    <div className="detail-columns">
      <div className="detail-main">
        <section className="detail-description"><div className="eyebrow muted">ABOUT THIS EVENT</div><h2>A reason to <em>show up.</em></h2><p>{event.description || 'No event description has been provided.'}</p></section>
        <Reviews reviews={reviews} summary={summary} ownReview={ownReview} onEdit={setEditingReview}/>
        {canReview && !ownReview && <ReviewComposer key={`new-${eventId}`} eventId={eventId} onCreated={handleReviewCreated}/>}
        {canReview && editingReview && <ReviewComposer key={`edit-${editingReview.id}`} eventId={eventId} existingReview={editingReview} onUpdated={handleReviewUpdated} onDeleted={handleReviewDeleted} onCancel={() => setEditingReview(null)}/>}
      </div>
      <aside className="registration-panel">
        <div className="eyebrow muted">{event.status === 'completed' ? 'EVENT COMPLETE' : 'SAVE YOUR PLACE'}</div>
        <h2>{event.status === 'completed' ? <>Thanks for<br/><em>showing up.</em></> : <>Be there<br/><em>in person.</em></>}</h2>
        <div className="capacity-line"><span>Event capacity</span><b>{event.capacity ?? 'Not specified'}</b></div>
        {event.status === 'completed' ? <div className="completed-event-note">Registration is closed. Confirmed attendees can share a review.</div> : !token ? <div className="login-prompt"><p>Sign in to register and keep your plans in one place.</p><Link to="/login" state={{ from: location.pathname }} className="register-cta">Sign in to register <span>→</span></Link></div> : registration ? <div className="registration-confirmation"><span>✓</span><b>You’re on the list</b><small>Status: {statusText}</small><Link to="/registrations" className="registration-link">View my registrations →</Link></div> : <><button className="register-cta" onClick={handleRegister} disabled={registering || registrationLoading}>{registrationLoading ? 'Checking registration…' : registering ? 'Registering…' : 'Register for event'} <span>→</span></button>{registerError && <p className="register-error" role="alert">{registerError}</p>}</>}
        <small className="capacity-note">Capacity is {event.capacity} attendees. Remaining seats aren’t provided by the API.</small>
      </aside>
    </div>
    <footer className="page-footer"><span>GOOD PLANS. GOOD PEOPLE.</span><span>MADE FOR SHOWING UP <b>✦</b></span></footer>
  </main>
}
