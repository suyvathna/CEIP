import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { createProject, updateProjectMilestones } from "../api/projects";

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
  // Not sent as part of ProjectCreate - see handleSubmit. Kept separate
  // on purpose so an edit to the project later (which reuses the create
  // schema) can never accidentally blank a milestone that isn't on that
  // form (see ProjectMilestonesUpdate's docstring in schemas/project.py).
  letter_of_acceptance_date: "",
  actual_commencement_date: "",
  defects_notification_period_days: 365,
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
  // Also milestone-pattern fields (see letter_of_acceptance_date above) -
  // sent through the same second call rather than ProjectCreate.
  progress_report_due_days: 7,
  statement_due_days: 7,
  compliance_alert_lead_days: 7,
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
      // These fields are deliberately NOT part of ProjectCreate (see the
      // field's comment above) - they go through the same milestones
      // PATCH the Compliance tab's register reads from, as a second call
      // right after creation, so this form's only job is to save the PM
      // a trip back to Compliance to set them.
      const {
        letter_of_acceptance_date,
        actual_commencement_date,
        defects_notification_period_days,
        progress_report_due_days,
        statement_due_days,
        compliance_alert_lead_days,
        ...projectFields
      } = formData;

      const newProject = await createProject({
        ...projectFields,
        duration_days: Number(formData.duration_days) || 0,
        contract_value: formData.contract_value === "" ? null : Number(formData.contract_value),
        notice_period_days: Number(formData.notice_period_days),
        detailed_claim_period_days: Number(formData.detailed_claim_period_days),
        engineer_late_notice_flag_days: Number(formData.engineer_late_notice_flag_days),
        engineer_response_period_days: Number(formData.engineer_response_period_days),
      });

      await updateProjectMilestones(newProject.id, {
        ...(letter_of_acceptance_date ? { letter_of_acceptance_date } : {}),
        ...(actual_commencement_date ? { actual_commencement_date } : {}),
        defects_notification_period_days: Number(defects_notification_period_days),
        progress_report_due_days: Number(progress_report_due_days),
        statement_due_days: Number(statement_due_days),
        compliance_alert_lead_days: Number(compliance_alert_lead_days),
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
          <legend>Contract Milestones &amp; Periods</legend>
          <label>
            Commencement date
            <input type="date" name="planned_start" value={formData.planned_start} onChange={handleChange} required />
          </label>
          <label>
            Actual Commencement Date (8.1)
            <input
              type="date"
              name="actual_commencement_date"
              value={formData.actual_commencement_date}
              onChange={handleChange}
            />
          </label>
          <p className="form-hint">
            Leave blank until work genuinely starts on Site - once set, the
            Target Completion Date and the Initial Programme deadline
            re-date from this instead of the Commencement date above.
          </p>
          <label>
            Letter of Acceptance (LOA) (1.1.51)
            <input
              type="date"
              name="letter_of_acceptance_date"
              value={formData.letter_of_acceptance_date}
              onChange={handleChange}
            />
          </label>
          <p className="form-hint">
            Starts the 28-day Performance Security (4.2) and Advance
            Payment guarantee (14.2) clocks. Leave blank if not yet
            issued — set it later from Edit Project.
          </p>
          <label>
            Time for Completion (Days)
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
            Defects Notification Period DNP (Days)
            <input
              type="number"
              min="1"
              name="defects_notification_period_days"
              value={formData.defects_notification_period_days}
              onChange={handleChange}
              required
            />
          </label>
        </fieldset>

        <fieldset>
          <legend>
            FIDIC subclause claim periods (days) - defaults are the
            unamended FIDIC 2017 Red Book; override if the Particular
            Conditions amend them
          </legend>
          <label>
            Notice of claim period (20.2.1)
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

        <fieldset>
          <legend>Other periods</legend>
          <label>
            Progress report due (days after month end)
            <input
              type="number"
              min="1"
              name="progress_report_due_days"
              value={formData.progress_report_due_days}
              onChange={handleChange}
              required
            />
          </label>
          <label>
            Statement due (days after month end)
            <input
              type="number"
              min="1"
              name="statement_due_days"
              value={formData.statement_due_days}
              onChange={handleChange}
              required
            />
          </label>
          <label>
            Alert lead time (days)
            <input
              type="number"
              min="1"
              name="compliance_alert_lead_days"
              value={formData.compliance_alert_lead_days}
              onChange={handleChange}
              required
            />
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
