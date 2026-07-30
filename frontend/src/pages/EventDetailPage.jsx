import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { getEvent, markNoticeGiven } from "../api/events";
import { getEventDiaries } from "../api/dailyDiaries";
import { getEventEvidence } from "../api/evidence";

const NOTICE_STATUS_LABELS = {
  pending: "Notice period open",
  overdue: "Notice deadline missed",
  given_on_time: "Notice given on time",
  given_late: "Notice given late",
};

// Local calendar date, not UTC - new Date().toISOString() shifts by the
// browser's UTC offset and would show yesterday's date for part of the day
// in Cambodia (UTC+7). This matches the same care taken on the backend.
function todayLocalISODate() {
  const d = new Date();
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function EventDetailPage() {
  const { projectId, eventId } = useParams();
  const [event, setEvent] = useState(null);
  const [diaries, setDiaries] = useState([]);
  const [evidence, setEvidence] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [noticeDate, setNoticeDate] = useState(todayLocalISODate());
  const [submittingNotice, setSubmittingNotice] = useState(false);

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

  async function handleMarkNoticeGiven(e) {
    e.preventDefault();
    setSubmittingNotice(true);
    try {
      const updated = await markNoticeGiven(eventId, noticeDate);
      setEvent(updated);
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmittingNotice(false);
    }
  }

  if (loading) return <p>Loading event...</p>;
  if (error) return <p>Something went wrong: {error}</p>;
  if (!event) return <p>Event not found.</p>;

  return (
    <div className="event-detail">
      <Link to={`/projects/${projectId}`}>&larr; Back to project</Link>
      <h1>{event.title}</h1>
      <p>
        {event.event_date}{" "}
        {event.event_time ? `at ${event.event_time}` : ""}
      </p>
      <p>
        {event.event_type} &mdash; {event.severity} severity
      </p>

      {event.status && (
        <span className={`status-badge status-${event.status.toLowerCase()}`}>
          {event.status}
        </span>
      )}

      {event.description && <p>{event.description}</p>}
      {event.location && <p>Location: {event.location}</p>}

      {/* FIDIC Notice Panel */}
      <div className="notice-panel">
        <h2>FIDIC Notice Deadline</h2>
        {event.notice_status && (
          <span className={`notice-badge notice-${event.notice_status}`}>
            {NOTICE_STATUS_LABELS[event.notice_status] || event.notice_status}
          </span>
        )}
        <p>
          Deadline: {event.notice_deadline || "N/A"}
          {event.notice_status === "pending" &&
            ` (${event.notice_days_remaining} day${
              event.notice_days_remaining === 1 ? "" : "s"
            } left)`}
          {event.notice_status === "overdue" &&
            ` (${Math.abs(event.notice_days_remaining)} day${
              Math.abs(event.notice_days_remaining) === 1 ? "" : "s"
            } overdue)`}
        </p>

        {event.notice_given_date ? (
          <p>Notice given on {event.notice_given_date}</p>
        ) : (
          <form onSubmit={handleMarkNoticeGiven} className="notice-form">
            <label>
              Mark notice as given on{" "}
              <input
                type="date"
                value={noticeDate}
                onChange={(e) => setNoticeDate(e.target.value)}
                required
              />
            </label>
            <button type="submit" disabled={submittingNotice}>
              {submittingNotice ? "Saving..." : "Mark Notice Given"}
            </button>
          </form>
        )}
      </div>

      {/* Diary Entries Section */}
      <div className="section-header">
        <h2>Diary Entries</h2>
        <Link to={`/projects/${projectId}/events/${eventId}/diary/new`}>
          + Add Diary
        </Link>
      </div>
      {diaries.length === 0 ? (
        <p>No diary entries yet.</p>
      ) : (
        diaries.map((diary) => (
          <div key={diary.id} className="diary-entry">
            <p>
              <strong>{diary.diary_date}</strong>
            </p>
            {diary.work_completed && <p>Work: {diary.work_completed}</p>}
            {diary.manpower !== null && diary.manpower !== undefined && (
              <p>Manpower: {diary.manpower}</p>
            )}
          </div>
        ))
      )}

      {/* Evidence Section */}
      <div className="section-header">
        <h2>Evidence</h2>
        <Link to={`/projects/${projectId}/events/${eventId}/evidence/new`}>
          + Add Evidence
        </Link>
      </div>
      {evidence.length === 0 ? (
        <p>No evidence uploaded yet.</p>
      ) : (
        evidence.map((item) => (
          <div key={item.id} className="evidence-item">
            {/* Fixed missing opening <a> tag */}
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