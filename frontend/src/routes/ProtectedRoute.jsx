import { useContext } from 'react'
import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { AuthContext } from '../context/AuthContext'

export default function ProtectedRoute() {
  const { token, user, authLoading } = useContext(AuthContext)
  const location = useLocation()
  if (authLoading) return <main className="content auth-wait"><div className="event-skeleton"/><p>Restoring your session…</p></main>
  if (!token || !user) return <Navigate to="/login" replace state={{ from: location.pathname }} />
  return <Outlet />
}
