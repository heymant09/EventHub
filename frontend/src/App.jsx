import { NavLink } from 'react-router-dom'
import Sidebar from './components/layout/Sidebar'
import Header from './components/layout/Header'
import AppRoutes from './routes/AppRoutes'

function Placeholder({ title }) { return <main className="content simple-page"><div className="eyebrow muted">EVENTHUB WORKSPACE</div><h1>{title}<em>.</em></h1><p>This workspace will connect to your EventHub account in the next implementation phase.</p><NavLink className="hero-cta" to="/">Back to discover <span>→</span></NavLink></main> }

export default function App() {
 return <div className="app-shell"><Sidebar/><div className="main-area"><Header/><AppRoutes Placeholder={Placeholder}/></div></div>
}
