import { useState } from "react";
import { useParams, Link as RouterLink } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useSnackbar } from "notistack";
import Typography from "@mui/material/Typography";
import Stack from "@mui/material/Stack";
import Paper from "@mui/material/Paper";
import Grid from "@mui/material/Grid";
import Button from "@mui/material/Button";
import Chip from "@mui/material/Chip";
import TextField from "@mui/material/TextField";
import MenuItem from "@mui/material/MenuItem";
import Divider from "@mui/material/Divider";
import CircularProgress from "@mui/material/CircularProgress";
import Alert from "@mui/material/Alert";
import List from "@mui/material/List";
import ListItem from "@mui/material/ListItem";
import ListItemText from "@mui/material/ListItemText";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import ContentCopyIcon from "@mui/icons-material/ContentCopy";
import DownloadIcon from "@mui/icons-material/Download";
import {
  getClaim,
  getClaimClock,
  getClaimEvents,
  getClaimDailyLogs,
  getClaimEvidenceList,
  getClaimRequirements,
  getEngineerDetermination,
  submitClaimNotice,
  flagClaimLateNotice,
  submitDetailedClaim,
  submitEngineerResponse,
  createClaimAccessLink,
  downloadClaimReportPdf,
  getClaimClauseOptions,
} from "../api/claims";
import {
  getClaimFacts,
  getClaimFactSummary,
  createClaimFact,
  respondToFact,
} from "../api/claimFacts";
import { getClaimDelayAnalysis } from "../api/programme";
import { getPublicClaimReportPdfUrl } from "../api/claimAccess";

const STAGE_STATUS_COLOR = {
  met: "success",
  missed: "error",
  overdue: "error",
  pending: "info",
  window_closed: "default",
};

function ClockPanel({ claimId }) {
  const clockQuery = useQuery({
    queryKey: ["claimClock", claimId],
    queryFn: () => getClaimClock(claimId),
  });

  if (clockQuery.isLoading) return <CircularProgress size={20} />;
  if (clockQuery.isError) return <Alert severity="error">{clockQuery.error.message}</Alert>;

  const clock = clockQuery.data;

  return (
    <Paper sx={{ p: 3 }}>
      <Typography variant="h6" gutterBottom>
        Sub-Clause 20.2 Deadline Clock
      </Typography>
      {clock.at_risk && (
        <Alert severity="warning" sx={{ mb: 2 }}>
          {clock.days_remaining < 0
            ? `${Math.abs(clock.days_remaining)} day(s) overdue on "${clock.next_action.label}".`
            : `Only ${clock.days_remaining} day(s) left on "${clock.next_action.label}".`}
        </Alert>
      )}
      <Stack spacing={1}>
        {clock.stages.map((stage) => (
          <Stack
            key={stage.stage}
            direction="row"
            spacing={2}
            sx={{ alignItems: "center", flexWrap: "wrap" }}
          >
            <Chip
              size="small"
              label={stage.status.replace("_", " ")}
              color={STAGE_STATUS_COLOR[stage.status] || "default"}
            />
            <Typography variant="body2" sx={{ flex: 1, minWidth: 240 }}>
              {stage.label}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Deadline: {stage.deadline}
              {stage.completed_date ? ` (done ${stage.completed_date})` : ""}
            </Typography>
          </Stack>
        ))}
      </Stack>
    </Paper>
  );
}

function ClaimRequirementsPanel({ claimId }) {
  const requirementsQuery = useQuery({
    queryKey: ["claimRequirements", claimId],
    queryFn: () => getClaimRequirements(claimId),
  });

  if (requirementsQuery.isLoading) return <CircularProgress size={20} />;
  if (requirementsQuery.isError) return null;

  const requirements = requirementsQuery.data;

  // No linked event carries a FIDIC-driven records checklist (e.g. a
  // purely operational event type, or no events linked yet) - nothing
  // useful to show, so skip the panel entirely rather than show an
  // empty "all satisfied" box that would be misleading.
  if (!requirements || requirements.events.length === 0) return null;

  return (
    <Paper sx={{ p: 3 }}>
      <Typography variant="h6" gutterBottom>
        Claim Readiness
      </Typography>
      {!requirements.all_satisfied && (
        <Alert severity="warning" sx={{ mb: 2 }}>
          {requirements.missing_count} required record(s) still missing across
          this claim's linked events. The fully detailed claim (Step 2 below)
          can't be submitted until these are attached.
        </Alert>
      )}
      {requirements.all_satisfied && (
        <Alert severity="success" sx={{ mb: 2 }}>
          All required records are attached for every linked event.
        </Alert>
      )}
      <Stack spacing={2}>
        {requirements.events.map((event) => (
          <div key={event.event_id}>
            <Typography variant="subtitle2">
              {event.event_no ? `${event.event_no} — ` : ""}
              {event.title}
            </Typography>
            <List dense disablePadding>
              {event.checklist.map((item) => (
                <ListItem key={item.kind} disableGutters>
                  <ListItemText
                    primary={`${item.satisfied ? "✓" : "✗"} ${item.label}`}
                    secondary={item.detail}
                  />
                </ListItem>
              ))}
            </List>
          </div>
        ))}
      </Stack>
    </Paper>
  );
}

function EngineerDeterminationPanel({ claimId }) {
  const determinationQuery = useQuery({
    queryKey: ["claimEngineerDetermination", claimId],
    queryFn: () => getEngineerDetermination(claimId),
  });

  return (
    <Paper sx={{ p: 3 }}>
      <Typography variant="h6" gutterBottom>
        Engineer's Determination
      </Typography>
      {determinationQuery.isLoading && <CircularProgress size={20} />}
      {!determinationQuery.isLoading && !determinationQuery.data && (
        <Typography variant="body2" color="text.secondary">
          No Engineer decision recorded yet.
        </Typography>
      )}
      {determinationQuery.data && (
        <Grid container spacing={2}>
          <Grid size={{ xs: 6, sm: 3 }}>
            <Typography variant="caption" color="text.secondary">
              Response type
            </Typography>
            <Typography variant="body1">{determinationQuery.data.response_type}</Typography>
          </Grid>
          <Grid size={{ xs: 6, sm: 3 }}>
            <Typography variant="caption" color="text.secondary">
              Response date
            </Typography>
            <Typography variant="body1">{determinationQuery.data.response_date}</Typography>
          </Grid>
          <Grid size={{ xs: 6, sm: 3 }}>
            <Typography variant="caption" color="text.secondary">
              EOT awarded (days)
            </Typography>
            <Typography variant="body1">
              {determinationQuery.data.eot_awarded_days ?? "—"}
            </Typography>
          </Grid>
          <Grid size={{ xs: 6, sm: 3 }}>
            <Typography variant="caption" color="text.secondary">
              Cost awarded
            </Typography>
            <Typography variant="body1">
              {determinationQuery.data.cost_awarded_amount ?? "—"}
            </Typography>
          </Grid>
          {determinationQuery.data.comment && (
            <Grid size={12}>
              <Typography variant="caption" color="text.secondary">
                Engineer's comment
              </Typography>
              <Typography variant="body2">{determinationQuery.data.comment}</Typography>
            </Grid>
          )}
          {determinationQuery.data.responded_by && (
            <Grid size={12}>
              <Typography variant="caption" color="text.secondary">
                Responded by: {determinationQuery.data.responded_by}
              </Typography>
            </Grid>
          )}
        </Grid>
      )}
    </Paper>
  );
}

function WorkflowActions({ claim, claimId, onChanged }) {
  const { enqueueSnackbar } = useSnackbar();
  const [noticeDate, setNoticeDate] = useState("");
  const [detailedDate, setDetailedDate] = useState("");
  const [legalBasis, setLegalBasis] = useState("");
  const [particulars, setParticulars] = useState("");
  const [responseType, setResponseType] = useState("Agreement");
  const [responseDate, setResponseDate] = useState("");
  const [daysGranted, setDaysGranted] = useState("");
  const [costAwarded, setCostAwarded] = useState("");
  const [responseComment, setResponseComment] = useState("");
  const [respondedBy, setRespondedBy] = useState("");
  const [flagDate, setFlagDate] = useState("");
  const [flagComment, setFlagComment] = useState("");

  const flagMutation = useMutation({
    mutationFn: () =>
      flagClaimLateNotice(claimId, { response_date: flagDate, comment: flagComment || null }),
    onSuccess: () => {
      enqueueSnackbar("Late-notice flag recorded", { variant: "success" });
      onChanged();
    },
    onError: (err) => enqueueSnackbar(err.message, { variant: "error" }),
  });

  const noticeMutation = useMutation({
    mutationFn: () => submitClaimNotice(claimId, { notice_submitted_date: noticeDate }),
    onSuccess: () => {
      enqueueSnackbar("Notice of Claim recorded", { variant: "success" });
      onChanged();
    },
    onError: (err) => enqueueSnackbar(err.message, { variant: "error" }),
  });

  const detailedMutation = useMutation({
    mutationFn: () =>
      submitDetailedClaim(claimId, {
        detailed_claim_submitted_date: detailedDate,
        legal_basis_statement: legalBasis,
        particulars,
      }),
    onSuccess: () => {
      enqueueSnackbar("Fully detailed claim recorded", { variant: "success" });
      onChanged();
    },
    onError: (err) => enqueueSnackbar(err.message, { variant: "error" }),
  });

  const responseMutation = useMutation({
    mutationFn: () =>
      submitEngineerResponse(claimId, {
        response_type: responseType,
        response_date: responseDate,
        days_granted: daysGranted === "" ? null : Number(daysGranted),
        cost_awarded_amount: costAwarded === "" ? null : Number(costAwarded),
        comment: responseComment || null,
        responded_by: respondedBy || null,
      }),
    onSuccess: () => {
      enqueueSnackbar("Engineer response recorded", { variant: "success" });
      onChanged();
    },
    onError: (err) => enqueueSnackbar(err.message, { variant: "error" }),
  });

  return (
    <Paper sx={{ p: 3 }}>
      <Typography variant="h6" gutterBottom>
        Workflow Actions
      </Typography>
      <Stack spacing={3} divider={<Divider />}>
        {!claim.notice_submitted_date && (
          <Stack spacing={1}>
            <Typography variant="subtitle2">1. Submit Notice of Claim (20.2.1)</Typography>
            <Stack direction="row" spacing={1} sx={{ alignItems: "center" }}>
              <TextField
                type="date"
                size="small"
                label="Notice submitted date"
                slotProps={{ inputLabel: { shrink: true } }}
                value={noticeDate}
                onChange={(e) => setNoticeDate(e.target.value)}
              />
              <Button
                variant="contained"
                size="small"
                disabled={!noticeDate || noticeMutation.isPending}
                onClick={() => noticeMutation.mutate()}
              >
                Submit
              </Button>
            </Stack>
          </Stack>
        )}

        {claim.notice_submitted_date && !claim.detailed_claim_submitted_date && (
          <Stack spacing={1}>
            <Typography variant="subtitle2">
              Engineer: flag this notice as late (20.2.2, optional)
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Must be done within the clock's late-notice flag window
              above, or the notice is deemed valid regardless of when it
              was actually submitted.
            </Typography>
            <Stack direction="row" spacing={1} sx={{ alignItems: "center", flexWrap: "wrap" }}>
              <TextField
                type="date"
                size="small"
                label="Flag date"
                slotProps={{ inputLabel: { shrink: true } }}
                value={flagDate}
                onChange={(e) => setFlagDate(e.target.value)}
              />
              <TextField
                size="small"
                label="Reason"
                value={flagComment}
                onChange={(e) => setFlagComment(e.target.value)}
              />
              <Button
                variant="outlined"
                color="warning"
                size="small"
                disabled={!flagDate || flagMutation.isPending}
                onClick={() => flagMutation.mutate()}
              >
                Flag as late
              </Button>
            </Stack>
          </Stack>
        )}

        {claim.notice_submitted_date && !claim.detailed_claim_submitted_date && (
          <Stack spacing={1}>
            <Typography variant="subtitle2">
              2. Submit fully detailed claim (20.2.4)
            </Typography>
            <TextField
              type="date"
              size="small"
              label="Submitted date"
              slotProps={{ inputLabel: { shrink: true } }}
              value={detailedDate}
              onChange={(e) => setDetailedDate(e.target.value)}
            />
            <TextField
              size="small"
              label="Statement of contractual/legal basis (required by 20.2.4)"
              multiline
              minRows={2}
              value={legalBasis}
              onChange={(e) => setLegalBasis(e.target.value)}
            />
            <TextField
              size="small"
              label="Detailed supporting particulars"
              multiline
              minRows={2}
              value={particulars}
              onChange={(e) => setParticulars(e.target.value)}
            />
            <Button
              variant="contained"
              size="small"
              sx={{ alignSelf: "flex-start" }}
              disabled={!detailedDate || !legalBasis || detailedMutation.isPending}
              onClick={() => detailedMutation.mutate()}
            >
              Submit detailed claim
            </Button>
          </Stack>
        )}

        {claim.detailed_claim_submitted_date && (
          <Stack spacing={1}>
            <Typography variant="subtitle2">
              3. Engineer's agreement or determination (20.2.5)
            </Typography>
            <TextField
              select
              size="small"
              label="Response type"
              value={responseType}
              onChange={(e) => setResponseType(e.target.value)}
            >
              {["Agreement", "PartialAgreement", "Disagreement", "Determination", "RequestForParticulars"].map(
                (t) => (
                  <MenuItem key={t} value={t}>
                    {t}
                  </MenuItem>
                )
              )}
            </TextField>
            <TextField
              type="date"
              size="small"
              label="Response date"
              slotProps={{ inputLabel: { shrink: true } }}
              value={responseDate}
              onChange={(e) => setResponseDate(e.target.value)}
            />
            <TextField
              type="number"
              size="small"
              label="Days granted (if applicable)"
              value={daysGranted}
              onChange={(e) => setDaysGranted(e.target.value)}
            />
            <TextField
              type="number"
              size="small"
              label="Cost awarded (if applicable)"
              value={costAwarded}
              onChange={(e) => setCostAwarded(e.target.value)}
            />
            <TextField
              size="small"
              label="Comment"
              multiline
              minRows={2}
              value={responseComment}
              onChange={(e) => setResponseComment(e.target.value)}
            />
            <TextField
              size="small"
              label="Responded by (Engineer name/email)"
              value={respondedBy}
              onChange={(e) => setRespondedBy(e.target.value)}
            />
            <Button
              variant="contained"
              size="small"
              sx={{ alignSelf: "flex-start" }}
              disabled={!responseDate || responseMutation.isPending}
              onClick={() => responseMutation.mutate()}
            >
              Record Engineer response
            </Button>
          </Stack>
        )}
      </Stack>
    </Paper>
  );
}

function FactsRegister({ claimId, onChanged }) {
  const { enqueueSnackbar } = useSnackbar();
  const factsQuery = useQuery({
    queryKey: ["claimFacts", claimId],
    queryFn: () => getClaimFacts(claimId),
  });
  const summaryQuery = useQuery({
    queryKey: ["claimFactSummary", claimId],
    queryFn: () => getClaimFactSummary(claimId),
  });

  const [description, setDescription] = useState("");
  const [agreedDays, setAgreedDays] = useState("");

  const addFactMutation = useMutation({
    mutationFn: () =>
      createClaimFact(claimId, {
        description,
        proposed_by_party: "Contractor",
        agreed_days: agreedDays === "" ? null : Number(agreedDays),
      }),
    onSuccess: () => {
      setDescription("");
      setAgreedDays("");
      onChanged();
    },
    onError: (err) => enqueueSnackbar(err.message, { variant: "error" }),
  });

  const respondMutation = useMutation({
    mutationFn: ({ factId, status, days, comment }) =>
      respondToFact(factId, {
        status,
        agreed_days: days,
        response_comment: comment,
        responded_by: "Engineer",
      }),
    onSuccess: () => onChanged(),
    onError: (err) => enqueueSnackbar(err.message, { variant: "error" }),
  });

  return (
    <Paper sx={{ p: 3 }}>
      <Typography variant="h6" gutterBottom>
        Fact-Agreement Register
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        Each fact is independently agreed or disputed, so the day-count
        separates what both parties already agree on from what's still
        contested.
      </Typography>

      {summaryQuery.data && (
        <Stack direction="row" spacing={3} sx={{ mb: 2, flexWrap: "wrap" }}>
          <Typography variant="body2">
            <strong>{summaryQuery.data.agreed_days_total}</strong> agreed days
          </Typography>
          <Typography variant="body2">
            <strong>{summaryQuery.data.disputed_days_total}</strong> disputed days
          </Typography>
          <Typography variant="body2">
            Contractor's ask: <strong>{summaryQuery.data.claimed_days ?? "—"}</strong>
          </Typography>
          <Typography variant="body2">
            {summaryQuery.data.agreed_facts}/{summaryQuery.data.total_facts} facts agreed
          </Typography>
        </Stack>
      )}

      {factsQuery.isLoading && <CircularProgress size={20} />}

      <List disablePadding>
        {factsQuery.data?.map((fact) => (
          <ListItem key={fact.id} divider sx={{ flexDirection: "column", alignItems: "stretch" }}>
            <Stack direction="row" spacing={1} sx={{ alignItems: "center", width: "100%" }}>
              <Chip
                size="small"
                label={fact.status}
                color={
                  fact.status === "Agreed"
                    ? "success"
                    : fact.status === "Disputed"
                    ? "error"
                    : fact.status === "NeedsEvidence"
                    ? "warning"
                    : "default"
                }
              />
              <Typography variant="body2" sx={{ flex: 1 }}>
                {fact.description}
                {fact.agreed_days != null ? ` (${fact.agreed_days} days)` : ""}
              </Typography>
            </Stack>
            {fact.status === "Proposed" && (
              <Stack direction="row" spacing={1} sx={{ mt: 1 }}>
                <Button
                  size="small"
                  color="success"
                  onClick={() =>
                    respondMutation.mutate({
                      factId: fact.id,
                      status: "Agreed",
                      days: fact.agreed_days,
                      comment: null,
                    })
                  }
                >
                  Agree
                </Button>
                <Button
                  size="small"
                  color="error"
                  onClick={() =>
                    respondMutation.mutate({
                      factId: fact.id,
                      status: "Disputed",
                      days: fact.agreed_days,
                      comment: "Disputed by Engineer",
                    })
                  }
                >
                  Dispute
                </Button>
                <Button
                  size="small"
                  onClick={() =>
                    respondMutation.mutate({
                      factId: fact.id,
                      status: "NeedsEvidence",
                      days: fact.agreed_days,
                      comment: "More evidence requested",
                    })
                  }
                >
                  Request evidence
                </Button>
              </Stack>
            )}
            {fact.response_comment && (
              <Typography variant="caption" color="text.secondary">
                {fact.responded_by || "Engineer"}: {fact.response_comment}
              </Typography>
            )}
          </ListItem>
        ))}
        {factsQuery.data?.length === 0 && (
          <Typography variant="body2" color="text.secondary">
            No facts proposed yet.
          </Typography>
        )}
      </List>

      <Stack spacing={1} sx={{ mt: 2 }}>
        <Typography variant="subtitle2">Propose a fact</Typography>
        <TextField
          size="small"
          label="Description"
          multiline
          minRows={2}
          value={description}
          onChange={(e) => setDescription(e.target.value)}
        />
        <TextField
          size="small"
          type="number"
          label="Days attributable to this fact (optional)"
          value={agreedDays}
          onChange={(e) => setAgreedDays(e.target.value)}
          sx={{ maxWidth: 260 }}
        />
        <Button
          variant="outlined"
          size="small"
          sx={{ alignSelf: "flex-start" }}
          disabled={!description || addFactMutation.isPending}
          onClick={() => addFactMutation.mutate()}
        >
          Add fact
        </Button>
      </Stack>
    </Paper>
  );
}

function DelayAnalysisPanel({ claimId, projectId }) {
  const analysisQuery = useQuery({
    queryKey: ["claimDelayAnalysis", claimId],
    queryFn: () => getClaimDelayAnalysis(claimId, projectId),
    retry: false,
  });

  return (
    <Paper sx={{ p: 3 }}>
      <Typography variant="h6" gutterBottom>
        Delay Analysis (Programme-based)
      </Typography>
      {analysisQuery.isLoading && <CircularProgress size={20} />}
      {analysisQuery.isError && (
        <Typography variant="body2" color="text.secondary">
          No programme activities recorded for this project yet. Add
          activities and link event impacts on the Programme tab to get a
          critical-path day-count for this claim.
        </Typography>
      )}
      {analysisQuery.data && (
        <Stack spacing={1}>
          <Grid container spacing={2}>
            <Grid size={{ xs: 6, sm: 3 }}>
              <Typography variant="caption" color="text.secondary">
                Contractor's ask
              </Typography>
              <Typography variant="h5">
                {analysisQuery.data.claimed_days ?? "—"}
              </Typography>
            </Grid>
            <Grid size={{ xs: 6, sm: 3 }}>
              <Typography variant="caption" color="text.secondary">
                Fact-register agreed
              </Typography>
              <Typography variant="h5">
                {analysisQuery.data.fact_register_agreed_days ?? "—"}
              </Typography>
            </Grid>
            <Grid size={{ xs: 6, sm: 3 }}>
              <Typography variant="caption" color="text.secondary">
                CPM critical delay
              </Typography>
              <Typography variant="h5">
                {analysisQuery.data.gross_critical_delay_days}
              </Typography>
            </Grid>
            <Grid size={{ xs: 6, sm: 3 }}>
              <Typography variant="caption" color="text.secondary">
                Absorbed by float
              </Typography>
              <Typography variant="h5">
                {analysisQuery.data.float_absorbed_days}
              </Typography>
            </Grid>
          </Grid>
          <Typography variant="body2" color="text.secondary">
            Baseline finish {analysisQuery.data.baseline_project_finish} →
            with this claim's impacts applied,{" "}
            {analysisQuery.data.claim_impacted_project_finish}.
          </Typography>
          {analysisQuery.data.overlapping_contractor_risk_events.length > 0 && (
            <Alert severity="info">
              {analysisQuery.data.overlapping_contractor_risk_events.length}{" "}
              concurrent Contractor-Risk event(s) overlap this claim's
              affected activities. Per the SCL Protocol these don't reduce
              this claim's entitlement on their own - review with the
              Engineer:{" "}
              {analysisQuery.data.overlapping_contractor_risk_events
                .map((e) => e.event_title)
                .join(", ")}
            </Alert>
          )}
          <Typography variant="caption" color="text.secondary">
            {analysisQuery.data.note}
          </Typography>
        </Stack>
      )}
    </Paper>
  );
}

function ShareReportPanel({ claimId }) {
  const { enqueueSnackbar } = useSnackbar();
  const [email, setEmail] = useState("");
  const [link, setLink] = useState(null);
  const [downloading, setDownloading] = useState(false);

  const linkMutation = useMutation({
    // recipient_email is optional server-side (see
    // ClaimAccessTokenCreate) - it's only kept for the Contractor's own
    // record, so an empty field should never block the link itself from
    // being generated.
    mutationFn: () => createClaimAccessLink(claimId, email || null),
    onSuccess: (token) => {
      setLink(getPublicClaimReportPdfUrl(token.token));
      enqueueSnackbar("Share link generated", { variant: "success" });
    },
    onError: (err) => enqueueSnackbar(err.message, { variant: "error" }),
  });

  async function handleDownload() {
    setDownloading(true);
    try {
      await downloadClaimReportPdf(claimId);
    } catch (err) {
      enqueueSnackbar(err.message, { variant: "error" });
    } finally {
      setDownloading(false);
    }
  }

  return (
    <Paper sx={{ p: 3 }}>
      <Typography variant="h6" gutterBottom>
        Share with the Engineer
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        CEIP is Contractor-only - the Engineer never logs in or gets an
        account. Download a read-only PDF of this claim to send yourself,
        or generate a link that opens straight to that same PDF. Either
        way, the only thing they can ever reach is the document itself.
      </Typography>

      <Button
        variant="contained"
        size="small"
        startIcon={<DownloadIcon fontSize="small" />}
        disabled={downloading}
        onClick={handleDownload}
      >
        {downloading ? "Preparing PDF..." : "Download claim report (PDF)"}
      </Button>

      <Divider sx={{ my: 2 }} />

      <Typography variant="subtitle2" gutterBottom>
        Or generate a share link
      </Typography>
      <Stack direction="row" spacing={1}>
        <TextField
          size="small"
          label="Engineer's email (optional, for your own record)"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
        <Button
          variant="outlined"
          disabled={linkMutation.isPending}
          onClick={() => linkMutation.mutate()}
        >
          {linkMutation.isPending ? "Generating..." : "Generate link"}
        </Button>
      </Stack>
      {link && (
        <Stack direction="row" spacing={1} sx={{ alignItems: "center", mt: 2 }}>
          <TextField
            size="small"
            fullWidth
            value={link}
            slotProps={{ input: { readOnly: true } }}
          />
          <Button
            size="small"
            startIcon={<ContentCopyIcon fontSize="small" />}
            onClick={() => navigator.clipboard.writeText(link)}
          >
            Copy
          </Button>
        </Stack>
      )}
    </Paper>
  );
}

function ClaimDetailPage() {
  const { projectId, claimId } = useParams();
  const queryClient = useQueryClient();

  const claimQuery = useQuery({
    queryKey: ["claim", claimId],
    queryFn: () => getClaim(claimId),
  });

  const eventsQuery = useQuery({
    queryKey: ["claimEvents", claimId],
    queryFn: () => getClaimEvents(claimId),
  });

  const dailyLogsQuery = useQuery({
    queryKey: ["claimDailyLogs", claimId],
    queryFn: () => getClaimDailyLogs(claimId),
  });

  const evidenceQuery = useQuery({
    queryKey: ["claimEvidenceList", claimId],
    queryFn: () => getClaimEvidenceList(claimId),
  });

  const clauseOptionsQuery = useQuery({
    queryKey: ["claimClauseOptions"],
    queryFn: getClaimClauseOptions,
  });

  function refreshAll() {
    queryClient.invalidateQueries({ queryKey: ["claim", claimId] });
    queryClient.invalidateQueries({ queryKey: ["claimClock", claimId] });
    queryClient.invalidateQueries({ queryKey: ["claimFacts", claimId] });
    queryClient.invalidateQueries({ queryKey: ["claimFactSummary", claimId] });
    queryClient.invalidateQueries({ queryKey: ["claimRequirements", claimId] });
    queryClient.invalidateQueries({ queryKey: ["claimEngineerDetermination", claimId] });
    queryClient.invalidateQueries({ queryKey: ["claims", projectId] });
  }

  if (claimQuery.isLoading) return <CircularProgress />;
  if (claimQuery.isError) return <Alert severity="error">{claimQuery.error.message}</Alert>;

  const claim = claimQuery.data;

  return (
    <Stack spacing={2}>
      <Button
        component={RouterLink}
        to={`/projects/${projectId}/claims`}
        size="small"
        startIcon={<ArrowBackIcon fontSize="small" />}
        sx={{ alignSelf: "flex-start" }}
      >
        Back to claims
      </Button>

      <Stack direction="row" spacing={1} sx={{ alignItems: "center", flexWrap: "wrap" }}>
        {claim.claim_no && (
          <Chip color="primary" variant="outlined" label={claim.claim_no} />
        )}
        <Typography variant="h4" fontWeight={700}>
          {claim.title}
        </Typography>
        <Chip label={claim.status} />
        <Chip variant="outlined" label={claim.claim_type} />
      </Stack>

      {claim.governing_clause && (
        <Typography variant="body2" color="text.secondary">
          Governing clause: {claim.governing_clause}
        </Typography>
      )}

      {claim.claim_basis &&
        (() => {
          const option = clauseOptionsQuery.data?.options?.find(
            (o) => o.event_type === claim.claim_basis
          );
          if (!option) return null;
          return (
            <Alert severity="info">
              Entitlement: {option.basis}
              <br />
              {option.summary}
            </Alert>
          );
        })()}

      {claim.description && (
        <Typography variant="body1" color="text.secondary">
          {claim.description}
        </Typography>
      )}

      <Paper sx={{ p: 3 }}>
        <Typography variant="subtitle2" gutterBottom>
          Linked events
        </Typography>
        {eventsQuery.data?.length ? (
          <List dense disablePadding>
            {eventsQuery.data.map((event) => (
              <ListItem key={event.id} disableGutters>
                <ListItemText
                  primary={`${event.event_no ? `${event.event_no} — ` : ""}${event.event_date} — ${event.title}`}
                  secondary={event.event_type}
                />
              </ListItem>
            ))}
          </List>
        ) : (
          <Typography variant="body2" color="text.secondary">
            No events linked.
          </Typography>
        )}

        <Divider sx={{ my: 2 }} />

        <Typography variant="subtitle2" gutterBottom>
          Linked Daily Log entries
        </Typography>
        {dailyLogsQuery.data?.length ? (
          <List dense disablePadding>
            {dailyLogsQuery.data.map((log) => (
              <ListItem key={log.id} disableGutters>
                <ListItemText primary={log.diary_date} />
              </ListItem>
            ))}
          </List>
        ) : (
          <Typography variant="body2" color="text.secondary">
            No Daily Log entries linked.
          </Typography>
        )}

        <Divider sx={{ my: 2 }} />

        <Typography variant="subtitle2" gutterBottom>
          Linked evidence
        </Typography>
        {evidenceQuery.data?.length ? (
          <List dense disablePadding>
            {evidenceQuery.data.map((item) => (
              <ListItem key={item.id} disableGutters>
                <ListItemText primary={item.filename || item.caption || `File ${item.id}`} />
              </ListItem>
            ))}
          </List>
        ) : (
          <Typography variant="body2" color="text.secondary">
            No evidence linked.
          </Typography>
        )}
      </Paper>

      <ClockPanel claimId={claimId} />
      <ClaimRequirementsPanel claimId={claimId} />
      <WorkflowActions claim={claim} claimId={claimId} onChanged={refreshAll} />
      <EngineerDeterminationPanel claimId={claimId} />
      <FactsRegister claimId={claimId} onChanged={refreshAll} />
      <DelayAnalysisPanel claimId={claimId} projectId={projectId} />
      <ShareReportPanel claimId={claimId} />
    </Stack>
  );
}

export default ClaimDetailPage;
