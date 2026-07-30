import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getAllEvents } from "../api/events";
import { getProjects } from "../api/projects";

const NOTICE_STATUS_LABELS = {
  pending: "Notice period open",
  overdue: "Notice deadline missed",
};

function DeadlinesDashboardPage() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    Promise.all([getAllEvents(), getProjects()])
      .then(([events, projects]) => {
        const projectNames = Object.fromEntries(
          projects.map((p) => [p.id, p.project_name])
        );

        const needsAttention = events
          .filter((event) => event.notice_given_date === null)
          .map((event) => ({
            ...event,
            project_name: projectNames[event.project_id] || "Unknown project",
          }))
          .sort((a, b) => a.notice_days_remaining - b.notice_days_remaining);

        setItems(needsAttention);
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p>Loading deadlines...</p>;
  if (error) return <p>Something went wrong: {error}</p>;

  return (
    <div className="deadlines-dashboard legacy-page">
      <h1>Notice Deadlines</h1>
      {items.length === 0 ? (
        <p>Nothing needs notice action right now.</p>
      ) : (
        items.map((event) => (
          <Link
            key={event.id}
            to={`/projects/${event.project_id}/events/${event.id}`}
            className="deadline-item"
          >
            <div className="deadline-item-header">
              <span className={`notice-badge notice-${event.notice_status}`}>
                {NOTICE_STATUS_LABELS[event.notice_status]}
              </span>
              <span className="deadline-days">
                {event.notice_status === "overdue"
                  ? `${Math.abs(event.notice_days_remaining)} day${Math.abs(event.notice_days_remaining) === 1 ? "" : "s"} overdue`
                  : `${event.notice_days_remaining} day${event.notice_days_remaining === 1 ? "" : "s"} left`}
              </span>
            </div>
            <h4>{event.title}</h4>
            <p>{event.project_name} &mdash; {event.event_date}</p>
            <p>Deadline: {event.notice_deadline}</p>
          </Link>
        ))
      )}
    </div>
  );
}

export default DeadlinesDashboardPage;