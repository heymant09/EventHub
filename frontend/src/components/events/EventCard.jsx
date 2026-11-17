import { Link } from 'react-router-dom'
import './EventCard.css'

export default function EventCard({ event, index }) {
  const start = new Date(event.start_time)
  const date = Number.isNaN(start.valueOf()) ? 'DATE TBA' : start.toLocaleDateString(undefined, { month: 'short', day: 'numeric' }).toUpperCase()
  const time = Number.isNaN(start.valueOf()) ? 'TIME TBA' : start.toLocaleTimeString(undefined, { hour: 'numeric', minute: '2-digit' })
  const palettes = ['#d8e5cd', '#edddcf', '#d8e1e9', '#e6e1c9']
  return <article className="event-card">
    <div className="event-card-art" style={{ background: palettes[index % palettes.length] }}>
      <span>EVENTHUB&nbsp; / &nbsp;{date}</span>
      <b>{event.categories?.[0]?.name || 'GATHER TOGETHER'}</b>
      <i>✳</i>
      <small>{event.status}</small>
    </div>
    <div className="event-card-body">
      <div className="event-date">{date}</div>
      <h3>{event.title}</h3>
      <p>{event.location}</p>
      <div className="event-card-bottom">
        <span>{time}</span>
        <Link to={`/events/${event.id}`} aria-label={`View event and register for ${event.title}`}>View &amp; register <b>↗</b></Link>
      </div>
    </div>
  </article>
}
