import { useContext, useState } from 'react'
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom'
import { login } from '../api/auth'
import { AuthContext } from '../context/AuthContext'
import './AuthPages.css'

function messageFrom(error) {
  const detail = error.response?.data?.detail
  if (Array.isArray(detail)) return detail.map((item) => item.msg).join(' ')
  return detail || 'Unable to sign in. Check your connection and try again.'
}

export default function LoginPage() {
  const { token, user, authLoading, setSession } = useContext(AuthContext)
  const navigate = useNavigate()
  const location = useLocation()
  const [form, setForm] = useState({ email: '', password: '' })
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  if (token && user) return <Navigate to={location.state?.from || '/'} replace />

  async function handleSubmit(event) {
    event.preventDefault(); setError('')
    if (!form.email.trim() || !form.password) { setError('Enter your email and password.'); return }
    setSubmitting(true)
    try {
      const result = await login({ email: form.email.trim(), password: form.password })
      setSession(result.access_token)
      navigate(location.state?.from || '/', { replace: true })
    } catch (err) { setError(messageFrom(err)) }
    finally { setSubmitting(false) }
  }

  return <main className="content auth-page"><div className="auth-card"><div className="auth-aside"><div className="auth-aside-mark">✳</div><div className="eyebrow">YOUR NEXT STORY</div><h2>Good to<br/>see you <em>again.</em></h2><p>Pick up where you left off. There’s always something worth showing up for.</p><div className="auth-aside-foot">EVENTHUB&nbsp; / &nbsp;COMMUNITY</div></div><section className="auth-form-wrap"><div className="eyebrow muted">WELCOME BACK</div><h1>Sign in<span>.</span></h1><p className="auth-subtitle">Enter your details and get back to making plans.</p><form onSubmit={handleSubmit} noValidate><label>Email address<input type="email" autoComplete="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} placeholder="you@example.com" required/></label><label>Password<div className="password-input"><input type={showPassword ? 'text' : 'password'} autoComplete="current-password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} placeholder="Your password" required/><button type="button" onClick={() => setShowPassword(!showPassword)}>{showPassword ? 'Hide' : 'Show'}</button></div></label>{error && <div className="auth-error" role="alert">{error}</div>}<button type="submit" className="auth-submit" disabled={submitting || (authLoading && Boolean(token))}>{submitting ? 'Signing in…' : 'Sign in'}<span>→</span></button></form><div className="auth-switch">New to EventHub? <Link to="/register">Create an account</Link></div></section></div></main>
}
