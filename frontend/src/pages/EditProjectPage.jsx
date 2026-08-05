import { useState, useEffect } from "react";
import { useNavigate, useParams, Link } from "react-router-dom";
import { getProject, updateProject, updateProjectMilestones } from "../api/projects";

const CURRENCIES = ["USD", "KHR", "THB", "EUR"];

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
          contract_no: project.contract_no || "",
          site_address: project.site_address || "",
          country: project.country,
          city: project.city,
          planned_start: project.planned_start,
          duration_days: project.duration_days,
          currency: project.currency || "USD",
          contract_value: project.contract_value ?? "",
          // Must be resent on every save - the update endpoint has no
          // partial-update semantics, so omitting these would silently
          // reset a project's claim-clock periods back to the FIDIC
          // defaults even if they'd been customized.
          notice_period_days: project.notice_period_days,
          detailed_claim_period_days: project.detailed_claim_period_days,
          engineer_late_notice_flag_days: project.engineer_late_notice_flag_days,
          engineer_response_period_days: project.engineer_response_period_days,
          // Milestone-pattern fields - saved through a separate
          // updateProjectMilestones() PATCH, same as on New Project (see
          // handleSubmit below).
          letter_of_acceptance_date: project.letter_of_acceptance_date || "",
          actual_commencement_date: project.actual_commencement_date || "",
          defects_notification_period_days: project.defects_notification_period_days,
          progress_report_due_days: project.progress_report_due_days,
          statement_due_days: project.statement_due_days,
          compliance_alert_lead_days: project.compliance_alert_lead_days,
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
      const {
        letter_of_acceptance_date,
        actual_commencement_date,
        defects_notification_period_days,
        progress_report_due_days,
        statement_due_days,
        compliance_alert_lead_days,
        ...projectFields
      } = formData;

      await updateProject(projectId, {
        ...projectFields,
        duration_days: Number(formData.duration_days) || 0,
        contract_value: formData.contract_value === "" ? null : Number(formData.contract_value),
        notice_period_days: Number(formData.notice_period_days),
        detailed_claim_period_days: Number(formData.detailed_claim_period_days),
        engineer_late_notice_flag_days: Number(formData.engineer_late_notice_flag_days),
        engineer_response_period_days: Number(formData.engineer_response_period_days),
      });

      await updateProjectMilestones(projectId, {
        letter_of_acceptance_date: letter_of_acceptance_date || null,
        actual_commencement_date: actual_commencement_date || null,
        defects_notification_period_days: Number(defects_notification_period_days),
        progress_report_due_days: Number(progress_report_due_days),
        statement_due_days: Number(statement_due_days),
        compliance_alert_lead_days: Number(compliance_alert_lead_days),
      });

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
          Contract No.
          <input name="contract_no" value={formData.contract_no} onChange={handleChange} />
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
          <input name="site_address" value={formData.site_address} onChange={handleChange} />
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
            Leave blank until work genuinely starts on Site - once set,
            the Target Completion Date and the Initial Programme deadline
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
            FIDIC subclause claim periods (days) - override if the
            Particular Conditions amend the unamended FIDIC 2017 defaults
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
          {submitting ? "Saving..." : "Save Changes"}
        </button>
      </form>
    </div>
  );
}

export default EditProjectPage;
