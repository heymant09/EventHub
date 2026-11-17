import { Link } from 'react-router-dom'
import { useContext } from 'react'
import { AuthContext } from '../../context/AuthContext'
import './Header.css'

export default function Header() {
  const { token, user, authLoading, logout } = useContext(AuthContext)
  const hasSession = Boolean(token || authLoading)

  return <header className="topbar">
    <div className="breadcrumb">EVENTHUB <span>/</span> <b>DISCOVER</b></div>
    <div className="top-actions">
      <div className="top-divider"/>
      {user ? <>
        <span className="account-label">Signed in as <b>{user.name}</b></span>
        <button type="button" className="logout-button" onClick={logout}>Log out</button>
      </> : hasSession ? <span className="account-loading">Restoring session…</span> : <>
        <Link to="/login" className="signin-link">Sign in <span>↗</span></Link>
        <Link to="/register" className="join-button">Create account <span>→</span></Link>
      </>}
    </div>
  </header>
}
