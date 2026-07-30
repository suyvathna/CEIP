import { useState } from "react";
import { useNavigate, useParams, Link } from "react-router-dom";
import { uploadEvidence } from "../api/evidence";

function NewEvidencePage() {
  const { projectId, eventId } = useParams();
  const [file, setFile] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

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
      await uploadEvidence(eventId, file);
      navigate(`/projects/${projectId}`);
    } catch (err) {
      setError(err.message);
      setSubmitting(false);
    }
  }

  return (
    <div className="new-evidence-page legacy-page">
      <Link to={`/projects/${projectId}`}>&larr; Back to project</Link>
      <h1>Upload Evidence</h1>
      <form onSubmit={handleSubmit}>
        <label>
          File
          <input type="file" onChange={handleFileChange} required />
        </label>

        {error && <p className="form-error">{error}</p>}

        <button type="submit" disabled={submitting}>
          {submitting ? "Uploading..." : "Upload"}
        </button>
      </form>
    </div>
  );
}

export default NewEvidencePage;