import { useState } from "react";
import { useNavigate, useParams, Link } from "react-router-dom";
import Button from "@mui/material/Button";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import { uploadEvidence } from "../api/evidence";

function NewEvidencePage() {
  const { projectId, eventId, dailyLogId, correspondenceId } = useParams();
  const [file, setFile] = useState(null);
  const [caption, setCaption] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  const backTo = eventId
    ? `/projects/${projectId}/events/${eventId}`
    : correspondenceId
      ? `/projects/${projectId}/correspondence/${correspondenceId}`
      : `/projects/${projectId}/daily-log/${dailyLogId}`;

  function handleFileChange(e) {
    setFile(e.target.files[0]);
  }

  async function handleSubmit(e) {
    e.preventDefault();
    if (!file) {
      setError("Please choose a file first.");
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      const owner = eventId
        ? { eventId }
        : correspondenceId
          ? { correspondenceId }
          : { dailyLogId };
      await uploadEvidence(owner, file, dailyLogId ? { caption } : {});
      navigate(backTo);
    } catch (err) {
      setError(err.message);
      setSubmitting(false);
    }
  }

  return (
    <div className="new-evidence-page legacy-page">
      <Button
        component={Link}
        to={backTo}
        size="small"
        startIcon={<ArrowBackIcon fontSize="small" />}
        sx={{ alignSelf: "flex-start" }}
      >
        Back
      </Button>
      <h1>Add Photo / Attachment</h1>
      <form onSubmit={handleSubmit}>
        <label>
          File
          <input type="file" accept="image/*,application/pdf" onChange={handleFileChange} required />
        </label>

        {dailyLogId && (
          <label>
            Caption
            <input
              type="text"
              value={caption}
              onChange={(e) => setCaption(e.target.value)}
              placeholder="e.g. V6 props (support) installation"
            />
          </label>
        )}

        {error && <p className="form-error">{error}</p>}

        <button type="submit" disabled={submitting}>
          {submitting ? "Uploading..." : "Upload"}
        </button>
      </form>
    </div>
  );
}

export default NewEvidencePage;
