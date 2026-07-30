import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getProjects } from "../api/projects";
import ProjectCard from "../components/ProjectCard";

function ProjectListPage() {
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    getProjects()
      .then(setProjects)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="project-list">
      <div className="page-header">
        <h1>Projects</h1>
        <Link to="/projects/new" className="new-project-button">
          + New Project
        </Link>
      </div>

      {loading && <p>Loading projects...</p>}
      {error && <p>Something went wrong: {error}</p>}
      {!loading && !error && projects.length === 0 && <p>No projects yet.</p>}

      {projects.map((project) => (
        <ProjectCard key={project.id} project={project} />
      ))}
    </div>
  );
}

export default ProjectListPage;