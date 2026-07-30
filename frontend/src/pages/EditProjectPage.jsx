import { useState, useEffect } from "react";
import { useNavigate, useParams, Link } from "react-router-dom";
import { getProject, updateProject } from "../api/projects";

function EditProjectPage() {
  const { projectId } = useParams();
  const [formData, setFormData] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    getProject(projectId)
      .then((project) => {
        setFormData({
          project_code: project.project_code,
          project_name: project.project_name,
          client_name: project.client_name,
          contractor_name: project.contractor_name || "",
          engineer_name: project.engineer_name || "",
          contract_type: project.contract_type,
          country: project.country,
          city: project.city,
          planned_start: project.planned_start,
          planned_finish: project.planned_finish,
        });
      })
      .catch((err) => setError(err.message));
  }, [projectId]);

  function handleChange(e) {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await updateProject(projectId, formData);
      navigate(`/projects/${projectId}`);
    } catch (err) {
      setError(err.message);
      setSubmitting(false);
    }
  }

  if (error && !formData) return <p>Something went wrong: {error}</p>;
  if (!formData) return <p>Loading...</p>;

  return (
    <div className="edit-project-page legacy-page">
      <Link to={`/projects/${projectId}`}>&larr; Back to project</Link>
      <h1>Edit Project</h1>
      <form onSubmit={handleSubmit}>
        <label>
          Project code
          <input name="project_code" value={formData.project_code} onChange={handleChange} required />
        </label>
        <label>
          Project name
          <input name="project_name" value={formData.project_name} onChange={handleChange} required />
        </label>
        <label>
          Client name
          <input name="client_name" value={formData.client_name} onChange={handleChange} required />
        </label>
        <label>
          Contractor name
          <input name="contractor_name" value={formData.contractor_name} onChange={handleChange} />
        </label>
        <label>
          Engineer name
          <input name="engineer_name" value={formData.engineer_name} onChange={handleChange} />
        </label>
        <label>
          Contract type
          <input name="contract_type" value={formData.contract_type} onChange={handleChange} required />
        </label>
        <label>
          Country
          <input name="country" value={formData.country} onChange={handleChange} required />
        </label>
        <label>
          City
          <input name="city" value={formData.city} onChange={handleChange} required />
        </label>
        <label>
          Planned start
          <input type="date" name="planned_start" value={formData.planned_start} onChange={handleChange} required />
        </label>
        <label>
          Planned finish
          <input type="date" name="planned_finish" value={formData.planned_finish} onChange={handleChange} required />
        </label>

        {error && <p className="form-error">{error}</p>}

        <button type="submit" disabled={submitting}>
          {submitting ? "Saving..." : "Save Changes"}
        </button>
      </form>
    </div>
  );
}

export default EditProjectPage;