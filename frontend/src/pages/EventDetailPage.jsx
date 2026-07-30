import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { getEvent } from "../api/events";
import { getEventDiaries } from "../api/dailyDiaries";
import { getEventEvidence } from "../api/evidence";

function EventDetailPage() {
  const { projectId, eventId } = useParams();
  const [event, setEvent] = useState(null);
  const [diaries, setDiaries] = useState([]);
  const [evidence, setEvidence] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      getEvent(eventId),
      getEventDiaries(eventId),
      getEventEvidence(eventId),
    ])
      .then(([eventData, diaryData, evidenceData]) => {
        setEvent(eventData);
        setDiaries(diaryData || []);
        setEvidence(evidenceData || []);
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [eventId]);

  if (loading) return <p>Loading event...</p>;
  if (error) return <p>Something went wrong: {error}</p>;
  if (!event) return <p>Event not found.</p>;

  return (
    <div className="event-detail">
      <Link to={`/projects/${projectId}`}>&larr; Back to project</Link>
      <h1>{event.title}</h1>
      <p>{event.event_date} {event.event_time ? `at ${event.event_time}` : ""}</p>
      <p>{event.event_type} &mdash; {event.severity} severity</p>
      
      {event.status && (
        <span className={`status-badge status-${event.status.toLowerCase()}`}>
          {event.status}
        </span>
      )}
      
      {event.description && <p>{event.description}</p>}
      {event.location && <p>Location: {event.location}</p>}

      <div className="section-header">
        <h2>Diary Entries</h2>
        <Link to={`/projects/${projectId}/events/${eventId}/diary/new`}>+ Add Diary</Link>
      </div>
      {diaries.length === 0 ? (
        <p>No diary entries yet.</p>
      ) : (
        diaries.map((diary) => (
          <div key={diary.id} className="diary-entry">
            <p><strong>{diary.diary_date}</strong></p>
            {diary.work_completed && <p>Work: {diary.work_completed}</p>}
            {diary.manpower !== null && diary.manpower !== undefined && (
              <p>Manpower: {diary.manpower}</p>
            )}
          </div>
        ))
      )}

      <div className="section-header">
        <h2>Evidence</h2>
        <Link to={`/projects/${projectId}/events/${eventId}/evidence/new`}>+ Add Evidence</Link>
      </div>
      {evidence.length === 0 ? (
        <p>No evidence uploaded yet.</p>
      ) : (
        evidence.map((item) => (
          <div key={item.id} className="evidence-item">
            {/* Fixed missing opening <a> tag here */}
            <a
              href={`${import.meta.env.VITE_API_BASE_URL}/evidence/download/${item.id}`}
              target="_blank"
              rel="noreferrer"
            >
              {item.filename || `File ${item.id}`}
            </a>
          </div>
        ))
      )}
    </div>
  );
}

export default EventDetailPage;