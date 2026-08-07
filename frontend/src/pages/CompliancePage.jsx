import { useEffect, useState } from "react";
import { useParams, useSearchParams, Link as RouterLink } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Typography from "@mui/material/Typography";
import Stack from "@mui/material/Stack";
import Paper from "@mui/material/Paper";
import Button from "@mui/material/Button";
import Chip from "@mui/material/Chip";
import Alert from "@mui/material/Alert";
import Divider from "@mui/material/Divider";
import CircularProgress from "@mui/material/CircularProgress";
import IconButton from "@mui/material/IconButton";
import Table from "@mui/material/Table";
import TableBody from "@mui/material/TableBody";
import TableCell from "@mui/material/TableCell";
import TableContainer from "@mui/material/TableContainer";
import TableHead from "@mui/material/TableHead";
import TableRow from "@mui/material/TableRow";
import Tabs from "@mui/material/Tabs";
import Tab from "@mui/material/Tab";
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
import AttachFileIcon from "@mui/icons-material/AttachFile";
import ProjectNav from "../components/ProjectNav";
import { todayLocalISODate } from "../utils/date";
import {
  getComplianceRegister,
  getComplianceRules,
  getEventDrivenRules,
  regenerateRegister,
  reopenObligation,
  submitObligation,
  waiveObligation,
} from "../api/compliance";
import { getProject, updateProjectMilestones } from "../api/projects";
import { uploadEvidence } from "../api/evidence";
import { BASE_URL } from "../api/client";

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

// The Compliance page's summary of contract milestones is a read-only
// mirror of the computed fields ProjectResponse exposes (see
// backend/app/schemas/project.py) - every row here is derived from the
// periods set on Project Creation, using the same formulas the register
// itself generates obligations from, so the two can never show different
// numbers for the same deadline.
const COMPUTED_MILESTONE_ROWS = [
  { key: "performance_security_submission_date", label: "Performance Security Submission (4.2.1)" },
  { key: "commencement_date_limit", label: "Commencement Date Limit (8.1)" },
  { key: "initial_programme_submission_date", label: "Initial Programme Submission (8.3)" },
  { key: "target_completion_date", label: "Target Completion Date" },
  { key: "statement_at_completion_due", label: "Statement at Completion Due" },
  { key: "dnp_expiry_date", label: "DNP Expiry Date" },
  { key: "performance_certificate_date", label: "Performance Certificate Date (11.9)" },
  { key: "return_of_performance_security_date", label: "Return of Performance Security (4.2.3)" },
  { key: "final_statement_submission_due_date", label: "Final Statement Submission Due (14.11.1)" },
];

function MilestonePanel({ projectId, project }) {
  const queryClient = useQueryClient();
  const [error, setError] = useState(null);

  const mutation = useMutation({
    mutationFn: (payload) => updateProjectMilestones(projectId, payload),
    onSuccess: () => {
      setError(null);
      queryClient.invalidateQueries({ queryKey: ["project", projectId] });
      queryClient.invalidateQueries({ queryKey: ["complianceRegister", projectId] });
      queryClient.invalidateQueries({ queryKey: ["complianceRules", projectId] });
      // Saving Actual TOC Date re-dates the register server-side, which
      // can retire or raise alerts - so the bell has to be refetched too,
      // or the badge sits there contradicting the screen.
      queryClient.invalidateQueries({ queryKey: ["notificationSummary"] });
      queryClient.invalidateQueries({ queryKey: ["notifications"] });
      queryClient.invalidateQueries({ queryKey: ["deadlineFeed"] });
    },
    onError: (e) => setError(e.message),
  });

  // No Save button on purpose - this is the one manual field left in an
  // otherwise read-only panel, so it saves the moment a date is picked
  // rather than leaving a button whose scope (just this field, not the
  // computed rows above) is easy to misread.
  function handleTakingOverChange(e) {
    mutation.mutate({ taking_over_date: e.target.value || null });
  }

  return (
    <Accordion>
      <AccordionSummary expandIcon={<ExpandMoreIcon />}>
        <Stack>
          <Typography variant="h6">Contract milestones &amp; periods</Typography>
          <Typography variant="caption" color="text.secondary">
            Computed from the dates and periods set on Project Creation. A
            blank row means its source date hasn't been entered yet —
            deliberately, since a deadline computed from a guessed date
            looks authoritative and is wrong.
          </Typography>
        </Stack>
      </AccordionSummary>

      <AccordionDetails>
        <Stack spacing={2}>
          {error && <Alert severity="error">{error}</Alert>}

          <TextField
            size="small"
            label="Contract edition"
            value="FIDIC 2017 Red Book 2nd Edition"
            slotProps={{ input: { readOnly: true } }}
          />

          <Grid container spacing={2}>
            {COMPUTED_MILESTONE_ROWS.map((row) => (
              <Grid key={row.key} size={{ xs: 12, sm: 6 }}>
                <TextField
                  fullWidth
                  size="small"
                  label={row.label}
                  value={project?.[row.key] || "—"}
                  slotProps={{ input: { readOnly: true } }}
                />
              </Grid>
            ))}
          </Grid>

          <Divider />

          <Paper variant="outlined" sx={{ p: 2 }}>
            <Stack spacing={1}>
              <Typography variant="subtitle2">Actual TOC Date (10.1)</Typography>
              <Typography variant="caption" color="text.secondary">
                Taking-Over Certificate date — the one milestone above that
                can&apos;t be computed. Saves as soon as you pick a date;
                every computed row above re-dates immediately.
              </Typography>
              <TextField
                key={project?.taking_over_date || "unset"}
                size="small"
                type="date"
                defaultValue={project?.taking_over_date || ""}
                onChange={handleTakingOverChange}
                disabled={mutation.isPending}
                slotProps={{ inputLabel: { shrink: true } }}
                sx={{ maxWidth: 220 }}
              />
              {mutation.isPending && (
                <Typography variant="caption" color="text.secondary">
                  Saving…
                </Typography>
              )}
            </Stack>
          </Paper>
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
  const [file, setFile] = useState(null);
  const [error, setError] = useState(null);

  const mutation = useMutation({
    mutationFn: async () => {
      // Uploaded first, ownerless until it's attached below, so a failed
      // submit doesn't leave a half-recorded obligation - only a stray
      // Evidence row, which is harmless and never surfaced anywhere.
      const evidence = file
        ? await uploadEvidence({ obligationId: obligation.id }, file)
        : null;
      return submitObligation(obligation.id, {
        submitted_date: submittedDate,
        submitted_reference: reference || null,
        evidence_id: evidence?.id || null,
        notes: notes || null,
      });
    },
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

          <Stack direction="row" spacing={1} sx={{ alignItems: "center" }}>
            <Button component="label" variant="outlined" size="small" startIcon={<AttachFileIcon fontSize="small" />}>
              {file ? "Replace file" : "Upload scanned letter / transmittal"}
              <input
                type="file"
                hidden
                onChange={(e) => setFile(e.target.files?.[0] || null)}
              />
            </Button>
            {file && (
              <>
                <Typography variant="body2" color="text.secondary">
                  {file.name}
                </Typography>
                <Button size="small" onClick={() => setFile(null)}>
                  Remove
                </Button>
              </>
            )}
          </Stack>

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
  const [file, setFile] = useState(null);
  const [error, setError] = useState(null);

  const mutation = useMutation({
    mutationFn: async () => {
      const evidence = file
        ? await uploadEvidence({ obligationId: obligation.id }, file)
        : null;
      return waiveObligation(obligation.id, {
        reason,
        evidence_id: evidence?.id || null,
      });
    },
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

          <Stack direction="row" spacing={1} sx={{ alignItems: "center" }}>
            <Button component="label" variant="outlined" size="small" startIcon={<AttachFileIcon fontSize="small" />}>
              {file ? "Replace file" : "Upload supporting document (optional)"}
              <input
                type="file"
                hidden
                onChange={(e) => setFile(e.target.files?.[0] || null)}
              />
            </Button>
            {file && (
              <>
                <Typography variant="body2" color="text.secondary">
                  {file.name}
                </Typography>
                <Button size="small" onClick={() => setFile(null)}>
                  Remove
                </Button>
              </>
            )}
          </Stack>
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

function trackedInLink(projectId, trackedIn) {
  switch (trackedIn) {
    case "Claims tab":
      return `/projects/${projectId}/claims`;
    case "Variations tab":
      return `/projects/${projectId}/claims?tab=variations`;
    case "Determinations tab":
      return `/projects/${projectId}/claims?tab=determinations`;
    case "Correspondence tab":
      return `/projects/${projectId}/correspondence`;
    default:
      return null;
  }
}

function EventDrivenTable({ projectId }) {
  const query = useQuery({
    queryKey: ["eventDrivenRules", projectId],
    queryFn: () => getEventDrivenRules(projectId),
  });

  const rules = query.data?.rules || [];

  return (
    <Stack spacing={2}>
      <Typography variant="body2" color="text.secondary">
        The notices and replies that only exist once something happens —
        a claim, a disputed instruction, a discovery on Site. Unlike the
        Always register, no due date is computed here: the deadline runs
        from the event, not from a fixed contract milestone. Where this
        platform already tracks a live instance of one of these, follow
        the link; for the rest, log it on the Correspondence tab as it
        goes out or comes in.
      </Typography>

      {query.isLoading && <CircularProgress size={24} />}
      {query.isError && <Alert severity="error">{query.error.message}</Alert>}

      {query.data && (
        <Alert severity="info">{query.data.disclaimer}</Alert>
      )}

      {rules.length > 0 && (
        <TableContainer component={Paper}>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Clause</TableCell>
                <TableCell>Document / Notice</TableCell>
                <TableCell>Direction</TableCell>
                <TableCell>Trigger</TableCell>
                <TableCell>Deadline</TableCell>
                <TableCell align="right">Track in</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {rules.map((rule) => {
                const link = trackedInLink(projectId, rule.tracked_in);
                return (
                  <TableRow key={rule.key} hover>
                    <TableCell sx={{ whiteSpace: "nowrap" }}>{rule.clause_code}</TableCell>
                    <TableCell>
                      <Tooltip title={rule.description}>
                        <Typography variant="body2">{rule.title}</Typography>
                      </Tooltip>
                    </TableCell>
                    <TableCell>
                      <Chip
                        size="small"
                        variant="outlined"
                        color={OWED_BY_COLORS[rule.direction] || "default"}
                        label={rule.direction}
                      />
                    </TableCell>
                    <TableCell sx={{ maxWidth: 260 }}>
                      <Typography variant="body2">{rule.trigger}</Typography>
                    </TableCell>
                    <TableCell sx={{ maxWidth: 220 }}>
                      <Typography variant="body2">{rule.deadline}</Typography>
                    </TableCell>
                    <TableCell align="right">
                      {link ? (
                        <Button size="small" component={RouterLink} to={link}>
                          {rule.tracked_in} →
                        </Button>
                      ) : (
                        <Typography variant="caption" color="text.secondary">
                          —
                        </Typography>
                      )}
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </TableContainer>
      )}
    </Stack>
  );
}

function CompliancePage() {
  const { projectId } = useParams();
  const queryClient = useQueryClient();
  const [searchParams, setSearchParams] = useSearchParams();
  const [docTab, setDocTab] = useState("always");
  const [statusFilter, setStatusFilter] = useState("");
  // Set from ?highlight=<obligation id> (see NotificationBell/deadline
  // feed link_paths) - scrolled to and flashed once the register has
  // loaded, then cleared so a later reload of this same URL doesn't
  // replay it.
  const highlightId = searchParams.get("highlight");
  const [flashId, setFlashId] = useState(highlightId);
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

  useEffect(() => {
    if (!highlightId || obligations.length === 0) return;

    // Re-set even when it's already this value - clicking a second alert
    // while already on this page changes highlightId but reuses the same
    // mounted component (no remount to re-run a useState initializer), so
    // without this the flash class - and the scroll below - would only
    // ever fire once per page load.
    setFlashId(highlightId);

    const row = document.getElementById(`obligation-row-${highlightId}`);
    row?.scrollIntoView({ behavior: "smooth", block: "center" });

    const timer = setTimeout(() => {
      setFlashId(null);
      const next = new URLSearchParams(searchParams);
      next.delete("highlight");
      setSearchParams(next, { replace: true });
    }, 3000);

    return () => clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [highlightId, obligations.length]);

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
        </Stack>
        <Stack direction="row" spacing={1}>
          {/* "Rebuild" was an engineer word for something that looked
              like it did nothing from outside. Named for what it
              changes, and reports its result. */}
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
        </Stack>
      </Stack>

      <Tabs
        value={docTab}
        onChange={(_, v) => setDocTab(v)}
        sx={{ borderBottom: 1, borderColor: "divider" }}
      >
        <Tab value="always" label="Always" />
        <Tab value="eventDriven" label="Event-Driven" />
      </Tabs>

      {docTab === "always" && (
        <>
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
                  <TableRow
                    key={row.id}
                    id={`obligation-row-${row.id}`}
                    hover
                    className={row.id === flashId ? "compliance-row-flash" : undefined}
                  >
                    <TableCell sx={{ whiteSpace: "nowrap" }}>
                      {row.clause_code}
                    </TableCell>
                    <TableCell>
                      <Tooltip title={rule?.description || ""}>
                        <Stack direction="row" spacing={1} sx={{ alignItems: "center" }}>
                          <Typography variant="body2">{row.title}</Typography>
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
                      <Stack direction="row" spacing={0.5} sx={{ justifyContent: "flex-end", alignItems: "center" }}>
                        {row.evidence_id && (
                          <Tooltip title="View attachment">
                            <IconButton
                              size="small"
                              component="a"
                              href={`${BASE_URL}/evidence/download/${row.evidence_id}`}
                              target="_blank"
                              rel="noreferrer"
                            >
                              <AttachFileIcon fontSize="small" />
                            </IconButton>
                          </Tooltip>
                        )}
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
        </>
      )}

      {docTab === "eventDriven" && <EventDrivenTable projectId={projectId} />}

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
