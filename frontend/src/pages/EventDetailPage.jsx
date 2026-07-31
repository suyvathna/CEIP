import { useEffect, useState } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { getEvent, markNoticeGiven, deleteEvent } from "../api/events";
import { getEventDiaries } from "../api/dailyDiaries";
import { getEventEvidence, deleteEvidence } from "../api/evidence";
import { BASE_URL } from "../api/client";
import { todayLocalISODate } from "../utils/date";

const NOTICE_STATUS_LABELS = {
  pending: "Notice period open",
  overdue: "Notice deadline missed",
  given_on_time: "Notice given on time",
  given_late: "Notice given late",
};

function EventDetailPage() {
  const { projectId, eventId } = useParams();
  const navigate = useNavigate();
  const [event, setEvent] = useState(null);
  const [diaries, setDiaries] = useState([]);
  const [evidence, setEvidence] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [deleteError, setDeleteError] = useState(null);
  const [attachmentError, setAttachmentError] = useState(null);
  const [noticeDate, setNoticeDate] = useState(todayLocalISODate());
  const [submittingNotice, setSubmittingNotice] = useState(false);

  function reload() {
    setLoading(true);
    return Promise.all([
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
  }

  useEffect(() => {
    reload();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [eventId]);

  async function handleDelete() {
    const confirmed = window.confirm(
      `Delete "${event.title}"? This cannot be undone.`
    );
    if (!confirmed) return;

    try {
      await deleteEvent(eventId);
      navigate(`/projects/${projectId}`);
    } catch (err) {
      setDeleteError(err.message);
    }
  }

  async function handleDeleteAttachment(item) {
    const confirmed = window.confirm(
      `Remove "${item.filename || "this attachment"}"? This cannot be undone.`
    );
    if (!confirmed) return;

    setAttachmentError(null);
    try {
      await deleteEvidence(item.id);
      setEvidence((prev) => prev.filter((e) => e.id !== item.id));
    } catch (err) {
      setAttachmentError(err.message);
    }
  }

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
    <div className="event-detail legacy-page">
      <Link to={`/projects/${projectId}`}>&larr; Back to project</Link>
      <div className="page-header">
        <h1>{event.title}</h1>
        <div className="project-actions">
          <Link to={`/projects/${projectId}/events/${eventId}/edit`}>Edit</Link>
          <button onClick={handleDelete} className="danger-button">Delete</button>
        </div>
      </div>
      {deleteError && <p className="form-error">{deleteError}</p>}
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

      {/* Diary Entries Section - read-only here. A diary is no longer
          created "from inside" an event: any Daily Diary entry logged for
          this project on the same date links to this event automatically
          (and vice versa). Add/edit diary entries from the project's
          Daily Diary tab instead. */}
      <div className="section-header">
        <h2>Linked Daily Diary</h2>
        <Link to={`/projects/${projectId}`}>Go to Daily Diary tab</Link>
      </div>
      {diaries.length === 0 ? (
        <p>
          No diary entry for {event.event_date} yet. Log one from the
          project's Daily Diary tab and it will link here automatically.
        </p>
      ) : (
        diaries.map((diary) => (
          <div key={diary.id} className="diary-entry">
            <p>
              <strong>{diary.diary_date}</strong>
            </p>
            {diary.work_completed && <p>Work: {diary.work_completed}</p>}
            {diary.manpower && <p>Manpower: {diary.manpower}</p>}
          </div>
        ))
      )}

      {/* Attachments Section (formerly "Evidence") */}
      <div className="section-header">
        <h2>Attachments</h2>
        <Link to={`/projects/${projectId}/events/${eventId}/evidence/new`}>
          + Add Attachment
        </Link>
      </div>
      {attachmentError && <p className="form-error">{attachmentError}</p>}
      {evidence.length === 0 ? (
        <p>No attachments yet.</p>
      ) : (
        evidence.map((item) => (
          <div key={item.id} className="evidence-item">
            <a
              href={`${BASE_URL}/evidence/download/${item.id}`}
              target="_blank"
              rel="noreferrer"
            >
              {item.filename || `File ${item.id}`}
            </a>
            {item.is_locked ? (
              <span className="status-badge" title="Attached to a submitted claim - can't be removed">
                {" "}
                Locked
              </span>
            ) : (
              <button
                type="button"
                className="danger-button"
                onClick={() => handleDeleteAttachment(item)}
              >
                Remove
              </button>
            )}
          </div>
        ))
      )}
    </div>
  );
}

export default EventDetailPage;