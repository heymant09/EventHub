import { Link, NavLink } from 'react-router-dom'
import { useContext } from 'react'
import { AuthContext } from '../../context/AuthContext'

export default function Sidebar() {
  const { user } = useContext(AuthContext)
  const links = [['Discover', '/', '⌕']]
  if (user) links.push(['My registrations', '/registrations', '▤'], ['My profile', '/profile', '◉'])
  if (['organiser', 'admin'].includes(user?.role)) links.push(['Organiser workspace', '/organiser', '◫'])
  if (user?.role === 'admin') links.push(['Admin workspace', '/admin', '⚙'])

  return <aside className="sidebar">
    <Link className="brand" to="/"><span className="brand-mark">e</span><span>event<span className="brand-light">hub</span><small>FIND YOUR NEXT MOMENT</small></span></Link>
    <div className="side-label">WORKSPACE</div>
    <nav>{links.map(([label, to, icon]) => <NavLink key={to} to={to} end={to === '/'} className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}><span className="nav-icon">{icon}</span>{label}</NavLink>)}</nav>
    <div className="sidebar-note"><div className="note-icon">✦</div><strong>Make room for<br/>something memorable.</strong><p>Discover gatherings, people and ideas worth showing up for.</p><Link to="/#browse">Explore events <span>↗</span></Link></div>
    <div className="sidebar-bottom"><span className="online-dot"/> EVENTHUB COMMUNITY <span className="version">v1.0</span></div>
  </aside>
}
