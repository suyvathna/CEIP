import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { getProject } from "../api/projects";
import { getProjectEvents } from "../api/events";
import EventList from "../components/EventList";

function ProjectDetailPage() {
  const { projectId } = useParams();
  const [project, setProject] = useState(null);
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    Promise.all([getProject(projectId), getProjectEvents(projectId)])
      .then(([projectData, eventsData]) => {
        setProject(projectData);
        setEvents(eventsData);
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [projectId]);

  if (loading) return <p>Loading project...</p>;
  if (error) return <p>Something went wrong: {error}</p>;

  return (
    <div className="project-detail">
      <Link to="/">&larr; Back to projects</Link>
      <h1>{project.project_name}</h1>
      <p>{project.project_code}</p>
      <p>Client: {project.client_name}</p>
      <p>Location: {project.city}, {project.country}</p>
      <p>Contract type: {project.contract_type}</p>
      <p>Status: {project.status}</p>
      <p>Planned: {project.planned_start} &rarr; {project.planned_finish}</p>

      <div className="events-section">
        <div className="section-header">
          <h2>Events</h2>
          <Link to={`/projects/${projectId}/events/new`} className="new-event-button">
            + New Event
          </Link>
        </div>
        <EventList events={events} />
      </div>
    </div>
  );
}

export default ProjectDetailPage;