import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { getCategories, getEvents } from '../api/events'
import EventCard from '../components/events/EventCard'
import EventFilters from '../components/events/EventFilters'

const PAGE_SIZE = 9
const toISO = (value) => {
  if (!value) return undefined
  const date = new Date(value)
  return Number.isNaN(date.valueOf()) ? undefined : date.toISOString()
}

function EventResults({ state, events, error, page, setPage, hasMore }) {
  if (state === 'loading') return <div className="event-grid">{Array.from({ length: 6 }, (_, i) => <div className="event-skeleton" key={i}/>)}</div>
  if (state === 'error') return <div className="result-state error-state"><b>We couldn’t load events.</b><p>{error}</p><button onClick={() => window.dispatchEvent(new Event('eventhub:retry-events'))}>Try again</button></div>
  if (!events.length) return <div className="result-state"><div className="empty-spark">✳</div><div><strong>{state === 'empty' && page === 0 ? 'No events available right now.' : 'No events found.'}</strong><p>Try a different search or clear a filter to see what’s happening.</p></div></div>
  return <><div className="event-grid">{events.map((event, index) => <EventCard key={event.id} event={event} index={index}/>)}</div><div className="pagination"><button disabled={page === 0} onClick={() => setPage(page - 1)}>← Previous</button><span>Page {page + 1}</span><button disabled={!hasMore} onClick={() => setPage(page + 1)}>Next →</button></div></>
}

export default function Discover() {
  const [events, setEvents] = useState([])
  const [categories, setCategories] = useState([])
  const [state, setState] = useState('loading')
  const [error, setError] = useState('')
  const [search, setSearch] = useState('')
  const [categoryId, setCategoryId] = useState('')
  const [sortBy, setSortBy] = useState('start_time')
  const [order, setOrder] = useState('asc')
  const [page, setPage] = useState(0)
  const [hasMore, setHasMore] = useState(false)
  const [retryCount, setRetryCount] = useState(0)
  const [showFilters, setShowFilters] = useState(false)
  const [filters, setFilters] = useState({ location: '', start_from: '', start_to: '' })
  const params = useMemo(() => ({ skip: page * PAGE_SIZE, limit: PAGE_SIZE, sort_by: sortBy, order, ...(search.trim() && { search: search.trim() }), ...(categoryId && { category_id: categoryId }), ...(filters.location.trim() && { location: filters.location.trim() }), ...(toISO(filters.start_from) && { start_from: toISO(filters.start_from) }), ...(toISO(filters.start_to) && { start_to: toISO(filters.start_to) }) }), [page, sortBy, order, search, categoryId, filters])

  useEffect(() => { setPage(0) }, [search, categoryId, sortBy, order, filters])
  useEffect(() => { getCategories().then(setCategories).catch(() => setCategories([])) }, [])
  useEffect(() => {
    let active = true
    const timer = setTimeout(async () => {
      setState('loading'); setError('')
      try {
        const data = await getEvents(params)
        if (active) { setEvents(data); setHasMore(data.length === PAGE_SIZE); setState(data.length ? 'success' : 'empty') }
      } catch (err) {
        if (active) { setError(err.response?.data?.detail || 'Check your connection and try again.'); setState('error') }
      }
    }, search ? 250 : 0)
    const retry = () => setRetryCount((count) => count + 1)
    window.addEventListener('eventhub:retry-events', retry)
    return () => { active = false; clearTimeout(timer); window.removeEventListener('eventhub:retry-events', retry) }
  }, [params, search, retryCount])

 return <main className="content" id="discover">
   <section className="hero"><div className="hero-copy"><div className="eyebrow"><span/> THE CITY IS YOURS TO EXPLORE</div><h1>Good things<br/>happen <em>together.</em></h1><p>Find your people, discover new passions and make the most of what’s happening around you.</p><a className="hero-cta" href="#browse">Explore what’s on <span>↘</span></a></div><div className="hero-art"><div className="sun"/><div className="art-ring ring-one"/><div className="art-ring ring-two"/><div className="art-card card-back"><small>YOUR NEXT STORY</small><b>starts here.</b><span>✳</span></div><div className="art-card card-front"><div className="ticket-top"><span>EH&nbsp; / &nbsp;LIVE</span><span>NO. 024</span></div><div className="ticket-shape">✳</div><div className="ticket-bottom"><b>Make a night of it.</b><span>GOOD PEOPLE · GREAT PLANS</span></div></div><div className="art-caption">A LITTLE MORE OUT THERE <span>✦</span></div></div><div className="hero-index"><span>01</span><i/> DISCOVER YOUR CITY</div></section>
   <section className="browse" id="browse"><div className="section-head"><div><div className="eyebrow muted">START WITH A SPARK</div><h2>Find your kind of <em>event.</em></h2></div><Link to="/" className="text-link">Browse all events <span>→</span></Link></div><EventFilters {...{search,setSearch,categories,categoryId,setCategoryId,filters,setFilters,sortBy,setSortBy,order,setOrder,showFilters,setShowFilters}}/><EventResults state={state} events={events} error={error} page={page} setPage={setPage} hasMore={hasMore}/></section>
   <footer className="page-footer"><span>GOOD PLANS. GOOD PEOPLE.</span><span>MADE FOR SHOWING UP <b>✦</b></span></footer>
 </main>
}
