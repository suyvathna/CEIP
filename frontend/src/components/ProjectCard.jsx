import { Link } from "react-router-dom";

function ProjectCard({ project }) {
  return (
    <Link to={`/projects/${project.id}`} className="project-card-link">
      <div className="project-card">
        <h3>{project.project_name}</h3>
        <p className="project-code">{project.project_code}</p>
        <p>{project.client_name}</p>
        <p>{project.city}, {project.country}</p>
        <span className={`status-badge status-${project.status.toLowerCase()}`}>
          {project.status}
        </span>
      </div>
    </Link>
  );
}

export default ProjectCard;