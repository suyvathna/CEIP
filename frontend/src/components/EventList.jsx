function EventList({ events }) {
  if (events.length === 0) {
    return <p>No events recorded yet.</p>;
  }

  return (
    <div className="event-list">
      {events.map((event) => (
        <div key={event.id} className="event-item">
          <h4>{event.title}</h4>
          <p>{event.event_date} at {event.event_time}</p>
          <p>{event.event_type} &mdash; {event.severity} severity</p>
          <span className={`status-badge status-${event.status.toLowerCase()}`}>
            {event.status}
          </span>
        </div>
      ))}
    </div>
  );
}

export default EventList;