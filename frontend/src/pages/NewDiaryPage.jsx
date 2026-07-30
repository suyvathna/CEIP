import { useState } from "react";
import { useNavigate, useParams, Link } from "react-router-dom";
import { createDailyDiary } from "../api/dailyDiaries";

const initialFormState = {
  diary_date: "",
  work_completed: "",
  manpower: "",
  equipment: "",
  materials: "",
  delays: "",
  safety: "",
  visitors: "",
  engineer_instruction: "",
  tomorrow_plan: "",
  remarks: "",
};

function NewDiaryPage() {
  const { projectId, eventId } = useParams();
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
      await createDailyDiary({
        ...formData,
        event_id: eventId,
        manpower: formData.manpower === "" ? null : Number(formData.manpower),
      });
      navigate(`/projects/${projectId}`);
    } catch (err) {
      setError(err.message);
      setSubmitting(false);
    }
  }

  return (
    <div className="new-diary-page">
      <Link to={`/projects/${projectId}`}>&larr; Back to project</Link>
      <h1>New Diary Entry</h1>
      <form onSubmit={handleSubmit}>
        <label>
          Diary date
          <input type="date" name="diary_date" value={formData.diary_date} onChange={handleChange} required />
        </label>
        <label>
          Work completed
          <textarea name="work_completed" value={formData.work_completed} onChange={handleChange} />
        </label>
        <label>
          Manpower (number of workers)
          <input type="number" name="manpower" value={formData.manpower} onChange={handleChange} min="0" />
        </label>
        <label>
          Equipment
          <textarea name="equipment" value={formData.equipment} onChange={handleChange} />
        </label>
        <label>
          Materials
          <textarea name="materials" value={formData.materials} onChange={handleChange} />
        </label>
        <label>
          Delays
          <textarea name="delays" value={formData.delays} onChange={handleChange} />
        </label>
        <label>
          Safety
          <textarea name="safety" value={formData.safety} onChange={handleChange} />
        </label>
        <label>
          Visitors
          <textarea name="visitors" value={formData.visitors} onChange={handleChange} />
        </label>
        <label>
          Engineer instruction
          <textarea name="engineer_instruction" value={formData.engineer_instruction} onChange={handleChange} />
        </label>
        <label>
          Tomorrow's plan
          <textarea name="tomorrow_plan" value={formData.tomorrow_plan} onChange={handleChange} />
        </label>
        <label>
          Remarks
          <textarea name="remarks" value={formData.remarks} onChange={handleChange} />
        </label>

        {error && <p className="form-error">{error}</p>}

        <button type="submit" disabled={submitting}>
          {submitting ? "Saving..." : "Save Diary Entry"}
        </button>
      </form>
    </div>
  );
}

export default NewDiaryPage;