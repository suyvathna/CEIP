import { useState, useEffect } from "react";
import { useNavigate, useParams, Link } from "react-router-dom";
import Button from "@mui/material/Button";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import { getEvent, updateEvent } from "../api/events";

// Must match app.constants.event_types.EventType on the backend exactly -
// same grouping as NewEventPage.jsx (kept in sync manually; see that
// file's comment for why this can't drift).
const EVENT_TYPE_GROUPS = [
  {
    label: "Operational",
    options: [
      "Progress", "Delay", "Weather", "Quality", "Safety", "RFI",
      "Instruction", "Inspection", "Delivery", "Incident",
      "Access Restriction", "Other",
    ],
  },
  {
    label: "FIDIC Red Book 2017 delay / claim grounds",
    options: [
      "Adverse Weather",
      "Design Change / Variation Order",
      "Delayed Drawings or Instructions",
      "Late Access to Site",
      "Errors in Setting-Out Data",
      "Unforeseeable Physical Conditions",
      "Fossils / Antiquities",
      "Employer-Instructed Additional Testing",
      "Delay Caused by Authorities",
      "Employer's Suspension of Work",
      "Interference with Tests on Completion",
      "Change in Laws",
      "Exceptional Event (Force Majeure)",
      "Epidemic / Government Action Shortage",
      "Contractor's Suspension for Non-Payment",
      "Late Payment by Employer",
      "Employer-Caused Delay (General)",
    ],
  },
];
const SEVERITIES = ["Low", "Medium", "High"];

function EditEventPage() {
  const { projectId, eventId } = useParams();
  const [formData, setFormData] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    getEvent(eventId)
      .then((event) => {
        setFormData({
          event_no: event.event_no || "",
          title: event.title,
          description: event.description || "",
          event_date: event.event_date,
          event_time: event.event_time,
          event_type: event.event_type,
          location: event.location || "",
          severity: event.severity,
        });
      })
      .catch((err) => setError(err.message));
  }, [eventId]);

  function handleChange(e) {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await updateEvent(eventId, { ...formData, project_id: projectId });
      navigate(`/projects/${projectId}/events/${eventId}`);
    } catch (err) {
      setError(err.message);
      setSubmitting(false);
    }
  }

  if (error && !formData) return <p>Something went wrong: {error}</p>;
  if (!formData) return <p>Loading...</p>;

  return (
    <div className="edit-event-page legacy-page">
      <Button
        component={Link}
        to={`/projects/${projectId}/events/${eventId}`}
        size="small"
        startIcon={<ArrowBackIcon fontSize="small" />}
        sx={{ alignSelf: "flex-start" }}
      >
        Back to event
      </Button>
      <h1>Edit Event</h1>
      <form onSubmit={handleSubmit}>
        <label>
          Event No.
          <input name="event_no" value={formData.event_no} onChange={handleChange} />
        </label>
        <label>
          Title
          <input name="title" value={formData.title} onChange={handleChange} required />
        </label>
        <label>
          Description
          <textarea name="description" value={formData.description} onChange={handleChange} />
        </label>
        <label>
          Date of Occurrence
          <input type="date" name="event_date" value={formData.event_date} onChange={handleChange} required />
        </label>
        <label>
          Time of Occurrence
          <input type="time" name="event_time" value={formData.event_time} onChange={handleChange} required />
        </label>
        <label>
          Event type
          <select name="event_type" value={formData.event_type} onChange={handleChange}>
            {EVENT_TYPE_GROUPS.map((group) => (
              <optgroup key={group.label} label={group.label}>
                {group.options.map((type) => (
                  <option key={type} value={type}>{type}</option>
                ))}
              </optgroup>
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
          {submitting ? "Saving..." : "Save Changes"}
        </button>
      </form>
    </div>
  );
}

export default EditEventPage;
