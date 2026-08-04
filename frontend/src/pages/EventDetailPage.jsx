import { useEffect, useState } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { getEvent, getEventRequirements, markNoticeGiven, deleteEvent } from "../api/events";
import { getEventDailyLogs } from "../api/dailyLogs";
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
  const [dailyLogs, setDailyLogs] = useState([]);
  const [evidence, setEvidence] = useState([]);
  const [requirements, setRequirements] = useState(null);
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
      getEventDailyLogs(eventId),
      getEventEvidence(eventId),
      getEventRequirements(eventId),
    ])
      .then(([eventData, dailyLogData, evidenceData, requirementsData]) => {
        setEvent(eventData);
        setDailyLogs(dailyLogData || []);
        setEvidence(evidenceData || []);
        setRequirements(requirementsData || null);
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
        <h1>{event.event_no ? `${event.event_no} — ${event.title}` : event.title}</h1>
        <div className="project-actions">
          <Link to={`/projects/${projectId}/events/${eventId}/edit`}>Edit</Link>
          <button onClick={handleDelete} className="danger-button">Delete</button>
        </div>
      </div>
      {deleteError && <p className="form-error">{deleteError}</p>}
      <p>
        Date of Occurrence: {event.event_date}{" "}
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

      {/* FIDIC Clause & Required Records Panel - only rendered when this
          event_type maps to a checklist (see event_requirements_service
          on the backend); purely operational event types return an
          empty checklist and this panel is skipped entirely. */}
      {requirements && requirements.checklist.length > 0 && (
        <div className="requirements-panel">
          <h2>FIDIC Claim Readiness</h2>

          {requirements.clause_reference && (
            <div className="clause-reference">
              <p>
                <strong>{requirements.clause_reference.clause_code}</strong>
                {" — "}
                {requirements.clause_reference.clause_title}
              </p>
              <p className="clause-basis">Entitlement: {requirements.clause_reference.basis}</p>
              <p className="clause-summary">{requirements.clause_reference.summary}</p>
              <p className="form-hint">
                Clause references are a drafting aid based on the unamended FIDIC
                Red Book 2017 General Conditions - always verify against this
                project's actual Particular Conditions before citing in a Notice
                of Claim.
              </p>
            </div>
          )}

          <p>
            {requirements.all_satisfied
              ? "All required records for this event type are attached."
              : "This event type needs the following records before a claim built on it is ready to submit:"}
          </p>
          <ul className="requirements-checklist">
            {requirements.checklist.map((item) => (
              <li
                key={item.kind}
                className={item.satisfied ? "requirement-met" : "requirement-missing"}
              >
                <span className="requirement-status">{item.satisfied ? "✓" : "✗"}</span>{" "}
                <strong>{item.label}</strong> — {item.detail}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Daily Log Section - read-only here. A Daily Log is no longer
          created "from inside" an event: any Daily Log entry logged for
          this project on the same date links to this event automatically
          (and vice versa). Add/edit Daily Log entries from the project's
          Daily Log tab instead. */}
      <div className="section-header">
        <h2>Linked Daily Log</h2>
        <Link to={`/projects/${projectId}`}>Go to Daily Log tab</Link>
      </div>
      {dailyLogs.length === 0 ? (
        <p>
          No Daily Log entry for {event.event_date} yet. Log one from the
          project's Daily Log tab and it will link here automatically.
        </p>
      ) : (
        dailyLogs.map((dailyLog) => (
          <div key={dailyLog.id} className="daily-log-entry">
            <p>
              <Link to={`/projects/${projectId}/daily-log/${dailyLog.id}`}>
                <strong>{dailyLog.diary_date}</strong>
              </Link>
            </p>
            {dailyLog.work_completed && <p>Work: {dailyLog.work_completed}</p>}
            {dailyLog.manpower_notes && <p>Manpower notes: {dailyLog.manpower_notes}</p>}
            {dailyLog.total_workers > 0 && (
              <p>
                {dailyLog.total_workers} workers logged ({dailyLog.total_man_hours} man-hours)
              </p>
            )}
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