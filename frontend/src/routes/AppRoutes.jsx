import { Navigate, Route, Routes } from 'react-router-dom'
import { useContext } from 'react'
import { AuthContext } from '../context/AuthContext'
import Discover from '../pages/Discover'
import EventDetails from '../pages/EventDetails'
import LoginPage from '../pages/LoginPage'
import RegisterPage from '../pages/RegisterPage'
import MyRegistrations from '../pages/MyRegistrations'
import OrganiserWorkspace from '../pages/OrganiserWorkspace'
import AdminWorkspace from '../pages/AdminWorkspace'
import ProfilePage from '../pages/ProfilePage'
import ProtectedRoute from './ProtectedRoute'
import RoleRoute from './RoleRoute'

function AuthOnly({ children }) {
  const { token, user, authLoading } = useContext(AuthContext)
  if (authLoading) return <main className="content auth-wait">Restoring your session…</main>
  return token && user ? <Navigate to="/" replace/> : children
}

export default function AppRoutes({ Placeholder }) {
  return <Routes>
    <Route path="/" element={<Discover/>}/>
    <Route path="/events/:eventId" element={<EventDetails/>}/>
    <Route path="/login" element={<AuthOnly><LoginPage/></AuthOnly>}/>
    <Route path="/register" element={<AuthOnly><RegisterPage/></AuthOnly>}/>
    <Route element={<ProtectedRoute/>}>
      <Route path="/registrations" element={<MyRegistrations/>}/>
      <Route path="/profile" element={<ProfilePage/>}/>
      <Route element={<RoleRoute roles={['organiser', 'admin']}/> }>
        <Route path="/organiser" element={<OrganiserWorkspace/>}/>
      </Route>
      <Route element={<RoleRoute roles={['admin']}/> }>
        <Route path="/admin" element={<AdminWorkspace/>}/>
      </Route>
    </Route>
    <Route path="*" element={<Placeholder title="Page not found"/>}/>
  </Routes>
}
