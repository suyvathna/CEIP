import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { createProject } from "../api/projects";

const CURRENCIES = ["USD", "KHR", "THB", "EUR"];

const initialFormState = {
  project_code: "",
  project_name: "",
  client_name: "",
  contractor_name: "",
  engineer_name: "",
  contract_type: "",
  contract_no: "",
  site_address: "",
  country: "Cambodia",
  city: "",
  planned_start: "",
  duration_days: "",
  currency: "USD",
  contract_value: "",
  // FIDIC 2017 Sub-Clause 20.2 default periods (days). These are
  // contract defaults, not fixed law - Particular Conditions (and the
  // MDB Harmonised Edition common on ADB/World Bank-funded work in
  // Cambodia) frequently amend them, so they're editable per project
  // rather than hardcoded.
  notice_period_days: 28,
  detailed_claim_period_days: 84,
  engineer_late_notice_flag_days: 14,
  engineer_response_period_days: 42,
};

// Local preview only - the authoritative completion date is always
// computed server-side from planned_start + duration_days (see
// project_service.py), this just shows the PM what to expect before
// they submit.
function previewCompletionDate(startDate, durationDays) {
  if (!startDate || !durationDays) return null;
  const start = new Date(`${startDate}T00:00:00`);
  if (Number.isNaN(start.getTime())) return null;
  const finish = new Date(start);
  finish.setDate(finish.getDate() + Number(durationDays));
  return finish.toISOString().slice(0, 10);
}

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
      const newProject = await createProject({
        ...formData,
        duration_days: Number(formData.duration_days) || 0,
        contract_value: formData.contract_value === "" ? null : Number(formData.contract_value),
        notice_period_days: Number(formData.notice_period_days),
        detailed_claim_period_days: Number(formData.detailed_claim_period_days),
        engineer_late_notice_flag_days: Number(formData.engineer_late_notice_flag_days),
        engineer_response_period_days: Number(formData.engineer_response_period_days),
      });
      navigate(`/projects/${newProject.id}`);
    } catch (err) {
      setError(err.message);
      setSubmitting(false);
    }
  }

  const completionPreview = previewCompletionDate(
    formData.planned_start,
    formData.duration_days
  );

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
          Contract No.
          <input
            name="contract_no"
            value={formData.contract_no}
            onChange={handleChange}
            placeholder="e.g. CT-2026-045"
          />
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
          Site address
          <input
            name="site_address"
            value={formData.site_address}
            onChange={handleChange}
            placeholder="Street, Sangkat/Commune, Khan/District, Province"
          />
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
          Commencement date
          <input type="date" name="planned_start" value={formData.planned_start} onChange={handleChange} required />
        </label>
        <label>
          Time for Completion (days)
          <input
            type="number"
            min="1"
            name="duration_days"
            value={formData.duration_days}
            onChange={handleChange}
            required
          />
        </label>
        {completionPreview && (
          <p className="form-hint">Completion date: {completionPreview}</p>
        )}
        <label>
          Currency
          <select name="currency" value={formData.currency} onChange={handleChange}>
            {CURRENCIES.map((c) => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
        </label>
        <label>
          Contract value
          <input
            type="number"
            min="0"
            step="0.01"
            name="contract_value"
            value={formData.contract_value}
            onChange={handleChange}
            placeholder="e.g. 2500000"
          />
        </label>

        <fieldset>
          <legend>
            FIDIC Sub-Clause 20.2 claim periods (days) - defaults are the
            unamended FIDIC 2017 Red Book; override if the Particular
            Conditions amend them
          </legend>
          <label>
            Notice of Claim period (20.2.1)
            <input type="number" min="1" name="notice_period_days" value={formData.notice_period_days} onChange={handleChange} required />
          </label>
          <label>
            Fully detailed claim period (20.2.4)
            <input type="number" min="1" name="detailed_claim_period_days" value={formData.detailed_claim_period_days} onChange={handleChange} required />
          </label>
          <label>
            Engineer's late-notice flag window (20.2.2)
            <input type="number" min="1" name="engineer_late_notice_flag_days" value={formData.engineer_late_notice_flag_days} onChange={handleChange} required />
          </label>
          <label>
            Engineer's response period (20.2.5)
            <input type="number" min="1" name="engineer_response_period_days" value={formData.engineer_response_period_days} onChange={handleChange} required />
          </label>
        </fieldset>

        {error && <p className="form-error">{error}</p>}

        <button type="submit" disabled={submitting}>
          {submitting ? "Creating..." : "Create Project"}
        </button>
      </form>
    </div>
  );
}

export default NewProjectPage;
