import { useState } from "react";
import { useNavigate, useParams, Link } from "react-router-dom";
import { createEvent } from "../api/events";

const EVENT_TYPES = [
  "Progress", "Delay", "Weather", "Quality", "Safety",
  "RFI", "Instruction", "Inspection", "Delivery", "Incident", "Other",
];
const SEVERITIES = ["Low", "Medium", "High"];

const initialFormState = {
  title: "",
  description: "",
  event_date: "",
  event_time: "",
  event_type: "Progress",
  location: "",
  severity: "Low",
};

function NewEventPage() {
  const { projectId } = useParams();
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
      await createEvent({ ...formData, project_id: projectId });
      navigate(`/projects/${projectId}`);
    } catch (err) {
      setError(err.message);
      setSubmitting(false);
    }
  }

  return (
    <div className="new-event-page">
      <Link to={`/projects/${projectId}`}>&larr; Back to project</Link>
      <h1>New Event</h1>
      <form onSubmit={handleSubmit}>
        <label>
          Title
          <input name="title" value={formData.title} onChange={handleChange} required />
        </label>
        <label>
          Description
          <textarea name="description" value={formData.description} onChange={handleChange} />
        </label>
        <label>
          Event date
          <input type="date" name="event_date" value={formData.event_date} onChange={handleChange} required />
        </label>
        <label>
          Event time
          <input type="time" name="event_time" value={formData.event_time} onChange={handleChange} required />
        </label>
        <label>
          Event type
          <select name="event_type" value={formData.event_type} onChange={handleChange}>
            {EVENT_TYPES.map((type) => (
              <option key={type} value={type}>{type}</option>
            ))}
          </select>
        </label>
        <label>
          Severity
          <select name="severity" value={formData.severity} onChange={handleChange}>
            {SEVERITIES.map((sev) => (
              <option key={sev} value={sev}>{sev}</option>
            ))}
          </select>
        </label>
        <label>
          Location
          <input name="location" value={formData.location} onChange={handleChange} />
        </label>

        {error && <p className="form-error">{error}</p>}

        <button type="submit" disabled={submitting}>
          {submitting ? "Creating..." : "Create Event"}
        </button>
      </form>
    </div>
  );
}

export default NewEventPage;