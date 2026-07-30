import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { createProject } from "../api/projects";

const initialFormState = {
  project_code: "",
  project_name: "",
  client_name: "",
  contractor_name: "",
  engineer_name: "",
  contract_type: "",
  country: "",
  city: "",
  planned_start: "",
  planned_finish: "",
};

function NewProjectPage() {
  const [formData, setFormData] = useState(initialFormState);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  function handleChange(e) {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const newProject = await createProject(formData);
      navigate(`/projects/${newProject.id}`);
    } catch (err) {
      setError(err.message);
      setSubmitting(false);
    }
  }

  return (
    <div className="new-project-page legacy-page">
      <Link to="/">&larr; Back to projects</Link>
      <h1>New Project</h1>
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
          {submitting ? "Creating..." : "Create Project"}
        </button>
      </form>
    </div>
  );
}

export default NewProjectPage;