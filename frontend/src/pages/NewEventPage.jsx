import { useState } from "react";
import { useNavigate, useParams, Link } from "react-router-dom";
import Button from "@mui/material/Button";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import { createEvent } from "../api/events";
import { uploadEvidence } from "../api/evidence";
import { todayLocalISODate, nowLocalTime } from "../utils/date";
import StagedAttachments from "../components/StagedAttachments";

// Must match app.constants.event_types.EventType on the backend exactly -
// the API validates event_type as a strict enum, so a mismatch here
// would fail on submit. Grouped into two <optgroup>s so the FIDIC Red
// Book 2017 delay/claim grounds (each one drives a required-records
// checklist and, later, a Claim's governing-clause auto-tag - see
// app/constants/fidic_clauses.py) are easy to find separately from the
// routine day-to-day categories.
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

const initialFormState = {
  // Left blank -> auto-generated "EVT-001" style per project (see
  // event_service._next_event_no); type one in only to match an
  // existing correspondence/RFI reference instead.
  event_no: "",
  title: "",
  description: "",
  // Defaults to today/now - most events are logged the same day they
  // happen, so this saves a tap on every single entry rather than
  // leaving the field blank and forcing a picker interaction each time.
  event_date: todayLocalISODate(),
  event_time: nowLocalTime(),
  event_type: "Progress",
  location: "",
  severity: "Low",
};

function NewEventPage() {
  const { projectId } = useParams();
  const [formData, setFormData] = useState(initialFormState);
  const [photos, setPhotos] = useState([]);
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
      const created = await createEvent({ ...formData, project_id: projectId });
      for (const staged of photos) {
        await uploadEvidence({ eventId: created.id }, staged.file);
      }
      navigate(`/projects/${projectId}/events/${created.id}`);
    } catch (err) {
      setError(err.message);
      setSubmitting(false);
    }
  }

  return (
    <div className="new-event-page legacy-page">
      <Button
        component={Link}
        to={`/projects/${projectId}/report`}
        size="small"
        startIcon={<ArrowBackIcon fontSize="small" />}
        sx={{ alignSelf: "flex-start" }}
      >
        Back to Site Records
      </Button>
      <h1>New Event</h1>
      <form onSubmit={handleSubmit}>
        <label>
          Event No.
          <input
            name="event_no"
            value={formData.event_no}
            onChange={handleChange}
            placeholder="Auto-generated (e.g. EVT-001) - leave blank unless matching your own reference"
          />
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

        <h2>Photos</h2>
        <StagedAttachments items={photos} onChange={setPhotos} addLabel="+ Add photo / attachment" />

        {error && <p className="form-error">{error}</p>}

        <button type="submit" disabled={submitting}>
          {submitting ? "Creating..." : "Create Event"}
        </button>
      </form>
    </div>
  );
}

export default NewEventPage;