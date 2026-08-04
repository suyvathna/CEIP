import { useState } from "react";
import { useParams, Link as RouterLink } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Typography from "@mui/material/Typography";
import Stack from "@mui/material/Stack";
import Paper from "@mui/material/Paper";
import Button from "@mui/material/Button";
import Chip from "@mui/material/Chip";
import Alert from "@mui/material/Alert";
import CircularProgress from "@mui/material/CircularProgress";
import Table from "@mui/material/Table";
import TableBody from "@mui/material/TableBody";
import TableCell from "@mui/material/TableCell";
import TableContainer from "@mui/material/TableContainer";
import TableHead from "@mui/material/TableHead";
import TableRow from "@mui/material/TableRow";
import TextField from "@mui/material/TextField";
import MenuItem from "@mui/material/MenuItem";
import Dialog from "@mui/material/Dialog";
import DialogTitle from "@mui/material/DialogTitle";
import DialogContent from "@mui/material/DialogContent";
import DialogActions from "@mui/material/DialogActions";
import Tooltip from "@mui/material/Tooltip";
import Accordion from "@mui/material/Accordion";
import AccordionSummary from "@mui/material/AccordionSummary";
import AccordionDetails from "@mui/material/AccordionDetails";
import Grid from "@mui/material/Grid";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import RefreshIcon from "@mui/icons-material/Refresh";
import ProjectNav from "../components/ProjectNav";
import EngineChip from "../components/EngineChip";
import EngineExplainer from "../components/EngineExplainer";
import { ENGINE_A } from "../utils/engines";
import { todayLocalISODate } from "../utils/date";
import {
  getComplianceRegister,
  getComplianceRules,
  regenerateRegister,
  reopenObligation,
  runComplianceTick,
  submitObligation,
  waiveObligation,
} from "../api/compliance";
import { getProject, updateProjectMilestones } from "../api/projects";

const STATUS_COLORS = {
  Pending: "default",
  DueSoon: "warning",
  Overdue: "error",
  Submitted: "success",
  SubmittedLate: "warning",
  Waived: "default",
  Superseded: "default",
};

const STATUS_LABELS = {
  Pending: "Open",
  DueSoon: "Due soon",
  Overdue: "Overdue",
  Submitted: "Submitted on time",
  SubmittedLate: "Submitted late",
  Waived: "Waived (N/A on this contract)",
  Superseded: "Superseded",
};

const OWED_BY_COLORS = {
  Contractor: "primary",
  Engineer: "secondary",
  Employer: "secondary",
};

const MILESTONE_FIELDS = [
  {
    name: "letter_of_acceptance_date",
    label: "Letter of Acceptance",
    type: "date",
    help: "Starts the 28-day Performance Security (4.2) and Advance Payment guarantee (14.2) clocks.",
  },
  {
    name: "taking_over_date",
    label: "Taking-Over Certificate (10.1)",
    type: "date",
    help: "Starts the 84-day Statement at Completion (14.10) and the Defects Notification Period. Also closes out the monthly obligations after it.",
  },
  {
    name: "performance_certificate_date",
    label: "Performance Certificate (11.9)",
    type: "date",
    help: "Starts the 56-day Final Statement clock (14.11) — the last door in the contract.",
  },
  {
    name: "defects_notification_period_days",
    label: "Defects Notification Period (days)",
    type: "number",
  },
  {
    name: "progress_report_due_days",
    label: "Progress report due (days after month end)",
    type: "number",
    help: "FIDIC fixes 7. Particular Conditions often change it.",
  },
  {
    name: "statement_due_days",
    label: "Statement due (days after month end)",
    type: "number",
    help: "The General Conditions fix no day for the monthly Statement, so set this to match what your contract or the Engineer's agreed procedure actually requires.",
  },
  {
    name: "compliance_alert_lead_days",
    label: "Alert lead time (days)",
    type: "number",
    help: "How far ahead of a deadline both engines start alerting.",
  },
];

function MilestonePanel({ projectId, project }) {
  const queryClient = useQueryClient();
  const [form, setForm] = useState(null);
  const [error, setError] = useState(null);

  const values =
    form ||
    Object.fromEntries(
      MILESTONE_FIELDS.map((field) => [
        field.name,
        project?.[field.name] ?? (field.type === "number" ? 0 : ""),
      ]).concat([["contract_edition", project?.contract_edition || "FIDIC 2017"]])
    );

  const mutation = useMutation({
    mutationFn: (payload) => updateProjectMilestones(projectId, payload),
    onSuccess: () => {
      setForm(null);
      setError(null);
      queryClient.invalidateQueries({ queryKey: ["project", projectId] });
      queryClient.invalidateQueries({ queryKey: ["complianceRegister", projectId] });
      queryClient.invalidateQueries({ queryKey: ["complianceRules", projectId] });
      // Saving a milestone re-dates the register server-side, which can
      // retire or raise alerts - so the bell has to be refetched too, or
      // the badge sits there contradicting the screen.
      queryClient.invalidateQueries({ queryKey: ["notificationSummary"] });
      queryClient.invalidateQueries({ queryKey: ["notifications"] });
      queryClient.invalidateQueries({ queryKey: ["deadlineFeed"] });
    },
    onError: (e) => setError(e.message),
  });

  function setField(name, value) {
    setForm({ ...values, [name]: value });
  }

  function handleSave() {
    // Only send what's actually set. Empty date strings become null so a
    // milestone can be cleared, but untouched numbers are sent as-is.
    const payload = { contract_edition: values.contract_edition };
    for (const field of MILESTONE_FIELDS) {
      const raw = values[field.name];
      if (field.type === "date") {
        payload[field.name] = raw ? raw : null;
      } else if (raw !== "" && raw !== null && raw !== undefined) {
        payload[field.name] = Number(raw);
      }
    }
    mutation.mutate(payload);
  }

  return (
    <Accordion>
      <AccordionSummary expandIcon={<ExpandMoreIcon />}>
        <Stack>
          <Typography variant="h6">Contract milestones &amp; periods</Typography>
          <Typography variant="caption" color="text.secondary">
            Everything below is what the engines measure from. A missing
            milestone means the obligations anchored on it simply are not
            generated — deliberately, since a deadline computed from a
            guessed date looks authoritative and is wrong.
          </Typography>
        </Stack>
      </AccordionSummary>

      <AccordionDetails>
        <Stack spacing={2}>
          {error && <Alert severity="error">{error}</Alert>}

          <TextField
            select
            size="small"
            label="Contract edition"
            value={values.contract_edition}
            onChange={(e) => setField("contract_edition", e.target.value)}
            helperText="Clause numbers move between editions — Progress Reports are Sub-Clause 4.20 under 2017 and 4.21 under 1999. This platform prints them straight into Notices."
          >
            <MenuItem value="FIDIC 2017">FIDIC 2017 (Red Book 2nd Ed.)</MenuItem>
            <MenuItem value="FIDIC 1999">FIDIC 1999 (Red Book 1st Ed. / MDB base)</MenuItem>
          </TextField>

          <Grid container spacing={2}>
            {MILESTONE_FIELDS.map((field) => (
              <Grid key={field.name} size={{ xs: 12, sm: 6 }}>
                <TextField
                  fullWidth
                  size="small"
                  type={field.type}
                  label={field.label}
                  value={values[field.name] ?? ""}
                  onChange={(e) => setField(field.name, e.target.value)}
                  helperText={field.help}
                  slotProps={{ inputLabel: { shrink: true } }}
                />
              </Grid>
            ))}
          </Grid>

          <Stack direction="row" spacing={1}>
            <Button
              variant="contained"
              onClick={handleSave}
              disabled={mutation.isPending}
            >
              Save milestones
            </Button>
            {form && (
              <Button onClick={() => setForm(null)} disabled={mutation.isPending}>
                Cancel
              </Button>
            )}
          </Stack>
        </Stack>
      </AccordionDetails>
    </Accordion>
  );
}

function SubmitDialog({ obligation, onClose, projectId }) {
  const queryClient = useQueryClient();
  const [submittedDate, setSubmittedDate] = useState(todayLocalISODate());
  const [reference, setReference] = useState("");
  const [notes, setNotes] = useState("");
  const [error, setError] = useState(null);

  const mutation = useMutation({
    mutationFn: () =>
      submitObligation(obligation.id, {
        submitted_date: submittedDate,
        submitted_reference: reference || null,
        notes: notes || null,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["complianceRegister", projectId] });
      queryClient.invalidateQueries({ queryKey: ["notificationSummary"] });
      queryClient.invalidateQueries({ queryKey: ["notifications"] });
      queryClient.invalidateQueries({ queryKey: ["deadlineFeed"] });
      onClose();
    },
    onError: (e) => setError(e.message),
  });

  const isLate = submittedDate > obligation.due_date;

  return (
    <Dialog open onClose={onClose} fullWidth maxWidth="sm">
      <DialogTitle>Record submission — {obligation.title}</DialogTitle>
      <DialogContent>
        <Stack spacing={2} sx={{ mt: 1 }}>
          {error && <Alert severity="error">{error}</Alert>}

          <Typography variant="body2" color="text.secondary">
            {obligation.clause_code} — due {obligation.due_date}
          </Typography>

          <TextField
            type="date"
            label="Date submitted"
            value={submittedDate}
            onChange={(e) => setSubmittedDate(e.target.value)}
            slotProps={{ inputLabel: { shrink: true } }}
          />

          {/* Recorded, not refused. A register that only accepts on-time
              entries stops being a record of what happened. */}
          {isLate && (
            <Alert severity="warning">
              This is after the deadline. It will be recorded as
              &ldquo;Submitted late&rdquo; — an honest record, not a cure.
            </Alert>
          )}

          <TextField
            label="Your reference (letter / transmittal no.)"
            value={reference}
            onChange={(e) => setReference(e.target.value)}
          />

          <TextField
            label="Notes"
            multiline
            minRows={2}
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
          />
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button
          variant="contained"
          onClick={() => mutation.mutate()}
          disabled={mutation.isPending}
        >
          Record
        </Button>
      </DialogActions>
    </Dialog>
  );
}

function WaiveDialog({ obligation, onClose, projectId }) {
  const queryClient = useQueryClient();
  const [reason, setReason] = useState("");
  const [error, setError] = useState(null);

  const mutation = useMutation({
    mutationFn: () => waiveObligation(obligation.id, reason),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["complianceRegister", projectId] });
      queryClient.invalidateQueries({ queryKey: ["notificationSummary"] });
      queryClient.invalidateQueries({ queryKey: ["notifications"] });
      onClose();
    },
    onError: (e) => setError(e.message),
  });

  return (
    <Dialog open onClose={onClose} fullWidth maxWidth="sm">
      <DialogTitle>Waive — {obligation.title}</DialogTitle>
      <DialogContent>
        <Stack spacing={2} sx={{ mt: 1 }}>
          {error && <Alert severity="error">{error}</Alert>}

          <Typography variant="body2" color="text.secondary">
            Use this where the rule genuinely does not apply to this
            contract — no advance payment was agreed, no monthly revised
            programme is required, and so on. A waiver survives every
            subsequent sweep.
          </Typography>

          <TextField
            label="Reason"
            required
            multiline
            minRows={2}
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            helperText="Required. A waiver with no stated reason is indistinguishable from someone clearing an inconvenient row, and this register is meant to survive being read back in a dispute."
          />
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button
          variant="contained"
          color="warning"
          onClick={() => mutation.mutate()}
          disabled={mutation.isPending || !reason.trim()}
        >
          Waive
        </Button>
      </DialogActions>
    </Dialog>
  );
}

function CompliancePage() {
  const { projectId } = useParams();
  const queryClient = useQueryClient();
  const [statusFilter, setStatusFilter] = useState("");
  const [submitTarget, setSubmitTarget] = useState(null);
  const [waiveTarget, setWaiveTarget] = useState(null);
  const [actionError, setActionError] = useState(null);
  // What the last Rebuild / sweep actually did. Succeeding silently is
  // what made these buttons feel broken: with nothing on screen, "it
  // worked and nothing needed changing" is indistinguishable from "it
  // did nothing".
  const [actionResult, setActionResult] = useState(null);

  const projectQuery = useQuery({
    queryKey: ["project", projectId],
    queryFn: () => getProject(projectId),
  });

  const rulesQuery = useQuery({
    queryKey: ["complianceRules", projectId],
    queryFn: () => getComplianceRules(projectId),
  });

  const registerQuery = useQuery({
    queryKey: ["complianceRegister", projectId, statusFilter],
    queryFn: () =>
      getComplianceRegister(projectId, { status: statusFilter || undefined }),
  });

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ["complianceRegister", projectId] });
    queryClient.invalidateQueries({ queryKey: ["notificationSummary"] });
    queryClient.invalidateQueries({ queryKey: ["notifications"] });
    queryClient.invalidateQueries({ queryKey: ["deadlineFeed"] });
  };

  const regenerateMutation = useMutation({
    mutationFn: () => regenerateRegister(projectId),
    onSuccess: (result) => {
      invalidate();
      setActionError(null);
      setActionResult(
        `Rebuilt: ${result.created} obligation(s) added, ${result.updated} re-dated or revived, ` +
          `${result.alerts} alert(s) raised, ${result.resolved} retired.`
      );
    },
    onError: (e) => setActionError(e.message),
  });

  const tickMutation = useMutation({
    mutationFn: runComplianceTick,
    onSuccess: (result) => {
      invalidate();
      setActionError(null);
      const run = result.run;
      setActionResult(
        result.ran && run
          ? `Sweep completed across ${run.projects_processed} project(s): ` +
              `${run.obligations_created} added, ${run.obligations_updated} updated, ` +
              `${run.notifications_created} alert(s) raised, ${run.notifications_resolved} retired.`
          : result.detail
      );
    },
    onError: (e) => setActionError(e.message),
  });

  const reopenMutation = useMutation({
    mutationFn: reopenObligation,
    onSuccess: () => {
      invalidate();
      setActionResult("Obligation reopened.");
    },
    onError: (e) => setActionError(e.message),
  });

  const summary = registerQuery.data?.summary;
  const obligations = registerQuery.data?.obligations || [];
  const rulesByKey = Object.fromEntries(
    (rulesQuery.data?.rules || []).map((rule) => [rule.key, rule])
  );

  return (
    <Stack spacing={2}>
      <Button
        component={RouterLink}
        to={`/projects/${projectId}`}
        size="small"
        startIcon={<ArrowBackIcon fontSize="small" />}
        sx={{ alignSelf: "flex-start" }}
      >
        Back to project
      </Button>

      <ProjectNav projectId={projectId} active="compliance" />

      <Stack
        direction="row"
        sx={{ justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 1 }}
      >
        <Stack direction="row" spacing={1.5} sx={{ alignItems: "center", flexWrap: "wrap" }}>
          <Typography variant="h4" fontWeight={700}>
            Compliance register
          </Typography>
          {/* This whole screen is Engine A. Claims, determinations and
              instructions live on their own tabs and belong to Engine B. */}
          <EngineChip engine={ENGINE_A} short={false} size="medium" />
        </Stack>
        <Stack direction="row" spacing={1}>
          {/* "Rebuild" and "Run sweep now" were engineer words for two
              things that looked identical from outside: both appeared to
              do nothing. Named for what they change, and both now report
              their result. */}
          <Tooltip title="Recompute every deadline on THIS project from its contract milestones. Use after editing the milestones above.">
            <span>
              <Button
                size="small"
                startIcon={<RefreshIcon fontSize="small" />}
                onClick={() => regenerateMutation.mutate()}
                disabled={regenerateMutation.isPending}
              >
                {regenerateMutation.isPending
                  ? "Recalculating…"
                  : "Recalculate this project"}
              </Button>
            </span>
          </Tooltip>
          <Tooltip title="Run the daily check across ALL projects now, instead of waiting for 06:00. Raises new alerts and retires ones that no longer apply.">
            <span>
              <Button
                size="small"
                variant="outlined"
                onClick={() => tickMutation.mutate()}
                disabled={tickMutation.isPending}
              >
                {tickMutation.isPending ? "Checking…" : "Check all projects now"}
              </Button>
            </span>
          </Tooltip>
        </Stack>
      </Stack>

      <Typography variant="body2" color="text.secondary">
        The obligations a FIDIC contract requires whether or not anything
        goes wrong on site. Nobody forgets to claim for a flooded site;
        plenty of teams forget that the progress report was due seven days
        after month end, or that the Final Statement has 56 days from the
        Performance Certificate and closes the contract for good.
      </Typography>

      {actionError && <Alert severity="error">{actionError}</Alert>}
      {actionResult && !actionError && (
        <Alert severity="success" onClose={() => setActionResult(null)}>
          {actionResult}
        </Alert>
      )}

      <EngineExplainer />

      {rulesQuery.data && (
        <Alert severity="info">{rulesQuery.data.disclaimer}</Alert>
      )}

      {projectQuery.data && (
        <MilestonePanel projectId={projectId} project={projectQuery.data} />
      )}

      {summary && (
        <Stack spacing={1}>
          <Stack direction="row" spacing={1} sx={{ flexWrap: "wrap", gap: 1 }}>
            <Chip color="primary" label={`${summary.live_open ?? summary.open} live`} />
            <Chip color="warning" label={`${summary.due_soon} due soon`} />
            <Chip color="error" label={`${summary.overdue} overdue`} />
            <Chip color="success" label={`${summary.submitted} submitted`} />
            <Chip color="warning" variant="outlined" label={`${summary.submitted_late} late`} />
            <Chip variant="outlined" label={`${summary.waived} waived`} />
          </Stack>

          {/* Separating these is the difference between "18 open" reading
              as a crisis and reading as "3 things to do, plus a backlog
              from before we started using the platform". */}
          {summary.historical_open > 0 && (
            <Alert severity="info">
              {summary.historical_open} of these fell due{" "}
              <strong>before this project was added to CEIP</strong>. They are
              kept in the register so you can record what was actually
              submitted or waive what never applied, but they do not raise
              individual alerts — one summary alert covers the whole backlog.
            </Alert>
          )}
        </Stack>
      )}

      <TextField
        select
        size="small"
        label="Filter by status"
        value={statusFilter}
        onChange={(e) => setStatusFilter(e.target.value)}
        sx={{ maxWidth: 280 }}
      >
        <MenuItem value="">All</MenuItem>
        {Object.entries(STATUS_LABELS).map(([value, label]) => (
          <MenuItem key={value} value={value}>
            {label}
          </MenuItem>
        ))}
      </TextField>

      {registerQuery.isLoading && <CircularProgress size={24} />}
      {registerQuery.isError && (
        <Alert severity="error">{registerQuery.error.message}</Alert>
      )}

      {registerQuery.data && obligations.length === 0 && (
        <Paper sx={{ p: 3 }}>
          <Typography color="text.secondary">
            Nothing in the register yet. Obligations are generated from the
            project&apos;s Commencement Date and its contract milestones —
            set those above, then press Rebuild.
          </Typography>
        </Paper>
      )}

      {obligations.length > 0 && (
        <TableContainer component={Paper}>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Clause</TableCell>
                <TableCell>Obligation</TableCell>
                <TableCell>Period</TableCell>
                <TableCell>Owed by</TableCell>
                <TableCell>Due</TableCell>
                <TableCell>Status</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {obligations.map((row) => {
                const rule = rulesByKey[row.rule_key];
                const closed = ["Waived", "Superseded"].includes(row.status);

                return (
                  <TableRow key={row.id} hover>
                    <TableCell sx={{ whiteSpace: "nowrap" }}>
                      {row.clause_code}
                    </TableCell>
                    <TableCell>
                      <Tooltip title={rule?.description || ""}>
                        <Stack direction="row" spacing={1} sx={{ alignItems: "center" }}>
                          <Typography variant="body2">{row.title}</Typography>
                          {/* Missing this forfeits an entitlement
                              outright rather than merely being a breach —
                              worth flagging in the register itself, not
                              only in the alert. */}
                          {row.rights_destroying && (
                            <Chip size="small" color="error" variant="outlined" label="Time-bar" />
                          )}
                          {row.is_historical && (
                            <Tooltip title="Fell due before this project was added to CEIP. Recorded as history — it does not raise its own alert.">
                              <Chip size="small" variant="outlined" label="Pre-CEIP" />
                            </Tooltip>
                          )}
                        </Stack>
                      </Tooltip>
                    </TableCell>
                    <TableCell>{row.period_key === "once" ? "—" : row.period_key}</TableCell>
                    <TableCell>
                      <Chip
                        size="small"
                        variant="outlined"
                        color={OWED_BY_COLORS[row.owed_by] || "default"}
                        label={row.owed_by}
                      />
                    </TableCell>
                    <TableCell sx={{ whiteSpace: "nowrap" }}>{row.due_date}</TableCell>
                    <TableCell>
                      <Chip
                        size="small"
                        color={STATUS_COLORS[row.status] || "default"}
                        label={STATUS_LABELS[row.status] || row.status}
                      />
                    </TableCell>
                    <TableCell align="right">
                      <Stack direction="row" spacing={0.5} sx={{ justifyContent: "flex-end" }}>
                        {!row.submitted_date && !closed && (
                          <Button size="small" onClick={() => setSubmitTarget(row)}>
                            Record
                          </Button>
                        )}
                        {!row.submitted_date && !closed && (
                          <Button size="small" color="warning" onClick={() => setWaiveTarget(row)}>
                            Waive
                          </Button>
                        )}
                        {(row.submitted_date || closed) && (
                          <Button
                            size="small"
                            onClick={() => reopenMutation.mutate(row.id)}
                            disabled={reopenMutation.isPending}
                          >
                            Reopen
                          </Button>
                        )}
                      </Stack>
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      {submitTarget && (
        <SubmitDialog
          obligation={submitTarget}
          projectId={projectId}
          onClose={() => setSubmitTarget(null)}
        />
      )}

      {waiveTarget && (
        <WaiveDialog
          obligation={waiveTarget}
          projectId={projectId}
          onClose={() => setWaiveTarget(null)}
        />
      )}
    </Stack>
  );
}

export default CompliancePage;
