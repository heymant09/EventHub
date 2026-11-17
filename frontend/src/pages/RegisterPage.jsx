import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { registerUser } from '../api/auth'
import './AuthPages.css'

function messageFrom(error) {
  const detail = error.response?.data?.detail
  if (Array.isArray(detail)) return detail.map((item) => item.msg).join(' ')
  if (detail) return detail
  if (error.code === 'ERR_NETWORK') return `Cannot reach the EventHub API at ${import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/v1'}. Check that FastAPI is running and CORS allows http://localhost:5173.`
  return error.message || 'Unable to create your account. Please try again.'
}

export default function RegisterPage() {
  const navigate = useNavigate()
  const [form, setForm] = useState({ name: '', email: '', password: '', confirmPassword: '' })
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(event) {
    event.preventDefault(); setError(''); setSuccess('')
    if (form.name.trim().length < 2) { setError('Name must contain at least 2 characters.'); return }
    if (!form.email.trim()) { setError('Enter a valid email address.'); return }
    if (form.password.length < 8) { setError('Password must be at least 8 characters.'); return }
    if (form.password !== form.confirmPassword) { setError('Passwords do not match.'); return }
    setSubmitting(true)
    try {
      await registerUser({ name: form.name.trim(), email: form.email.trim(), password: form.password })
      setSuccess('Your attendee account is ready. Taking you to sign in…')
      setTimeout(() => navigate('/login', { replace: true, state: { registered: true } }), 900)
    } catch (err) { setError(messageFrom(err)) }
    finally { setSubmitting(false) }
  }

  return <main className="content auth-page"><div className="auth-card"><div className="auth-aside register-aside"><div className="auth-aside-mark">✦</div><div className="eyebrow">MAKE ROOM FOR MORE</div><h2>Find your<br/>people <em>here.</em></h2><p>From small gatherings to big nights out, it starts with showing up.</p><div className="auth-aside-foot">EVENTHUB&nbsp; / &nbsp;COMMUNITY</div></div><section className="auth-form-wrap"><div className="eyebrow muted">JOIN THE COMMUNITY</div><h1>Create account<span>.</span></h1><p className="auth-subtitle">A few details and you’re in.</p><form onSubmit={handleSubmit} noValidate><label>Your name<input autoComplete="name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="Your name" required/></label><label>Email address<input type="email" autoComplete="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} placeholder="you@example.com" required/></label><label>Password<div className="password-input"><input type={showPassword ? 'text' : 'password'} autoComplete="new-password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} placeholder="At least 8 characters" required/><button type="button" onClick={() => setShowPassword(!showPassword)}>{showPassword ? 'Hide' : 'Show'}</button></div></label><label>Confirm password<input type={showPassword ? 'text' : 'password'} autoComplete="new-password" value={form.confirmPassword} onChange={(e) => setForm({ ...form, confirmPassword: e.target.value })} placeholder="Enter password again" required/></label>{error && <div className="auth-error" role="alert">{error}</div>}{success && <div className="auth-success" role="status">{success}</div>}<button type="submit" className="auth-submit" disabled={submitting}>{submitting ? 'Creating account…' : 'Create attendee account'}<span>→</span></button></form><div className="auth-switch">Already have an account? <Link to="/login">Sign in</Link></div></section></div></main>
}
