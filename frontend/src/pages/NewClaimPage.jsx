import { useMemo, useState } from "react";
import { useParams, useNavigate, Link as RouterLink } from "react-router-dom";
import { useQuery, useMutation, useQueries } from "@tanstack/react-query";
import Typography from "@mui/material/Typography";
import Stack from "@mui/material/Stack";
import Paper from "@mui/material/Paper";
import TextField from "@mui/material/TextField";
import MenuItem from "@mui/material/MenuItem";
import Button from "@mui/material/Button";
import FormGroup from "@mui/material/FormGroup";
import FormControlLabel from "@mui/material/FormControlLabel";
import Checkbox from "@mui/material/Checkbox";
import Alert from "@mui/material/Alert";
import CircularProgress from "@mui/material/CircularProgress";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import { getProjectEvents } from "../api/events";
import { getProjectDailyLogs } from "../api/dailyLogs";
import { getEventEvidence, getDailyLogEvidence } from "../api/evidence";
import { createClaim, getClaimClauseOptions } from "../api/claims";

const CLAIM_TYPES = ["EOT", "Cost", "EOT+Cost"];
const CLAIMING_PARTIES = ["Contractor", "Employer"];
const OTHER_CLAUSE_VALUE = "__other__";

function NewClaimPage() {
  const { projectId } = useParams();
  const navigate = useNavigate();

  const eventsQuery = useQuery({
    queryKey: ["projectEvents", projectId],
    queryFn: () => getProjectEvents(projectId),
  });

  const dailyLogsQuery = useQuery({
    queryKey: ["projectDailyLogs", projectId],
    queryFn: () => getProjectDailyLogs(projectId),
  });

  const clauseOptionsQuery = useQuery({
    queryKey: ["claimClauseOptions"],
    queryFn: getClaimClauseOptions,
  });

  const [form, setForm] = useState({
    claim_no: "",
    governing_clause: "",
    claim_basis: "",
    claim_type: "EOT",
    claiming_party: "Contractor",
    title: "",
    description: "",
    awareness_date: "",
    claimed_days: "",
    claimed_cost_amount: "",
  });
  const [clauseSelection, setClauseSelection] = useState("");
  const [selectedEventIds, setSelectedEventIds] = useState([]);
  const [selectedDailyLogIds, setSelectedDailyLogIds] = useState([]);
  const [selectedEvidenceIds, setSelectedEvidenceIds] = useState([]);

  // Attaching an Event or Daily Log to a claim commonly means its
  // evidence belongs to the claim too - rather than force a separate
  // project-wide evidence browser, the Evidence picker below is built
  // from whatever's already attached to the events/daily logs the
  // Contractor just selected above.
  const eventEvidenceQueries = useQueries({
    queries: selectedEventIds.map((id) => ({
      queryKey: ["eventEvidence", id],
      queryFn: () => getEventEvidence(id),
    })),
  });
  const dailyLogEvidenceQueries = useQueries({
    queries: selectedDailyLogIds.map((id) => ({
      queryKey: ["dailyLogEvidence", id],
      queryFn: () => getDailyLogEvidence(id),
    })),
  });

  const availableEvidence = useMemo(() => {
    const all = [
      ...eventEvidenceQueries.flatMap((q) => q.data || []),
      ...dailyLogEvidenceQueries.flatMap((q) => q.data || []),
    ];
    const byId = new Map(all.map((item) => [item.id, item]));
    return [...byId.values()];
  }, [eventEvidenceQueries, dailyLogEvidenceQueries]);

  const clauseOptions = clauseOptionsQuery.data?.options || [];

  function handleClauseChange(value) {
    setClauseSelection(value);

    if (value === "" || value === OTHER_CLAUSE_VALUE) {
      setForm((prev) => ({ ...prev, claim_basis: "" }));
      return;
    }

    const option = clauseOptions.find((o) => o.event_type === value);
    if (!option) return;

    setForm((prev) => ({
      ...prev,
      claim_basis: option.event_type,
      governing_clause: `${option.clause_code} - ${option.clause_title}`,
    }));
  }

  const selectedClauseOption = clauseOptions.find(
    (o) => o.event_type === clauseSelection
  );

  // Evidence checkboxes are only rendered for whatever's currently in
  // availableEvidence (derived from the selected events/daily logs
  // above), but selectedEvidenceIds itself isn't pruned when that pool
  // shrinks (e.g. unchecking the event a photo came from) - intersecting
  // here at submit time is simpler than syncing state in an effect, and
  // avoids sending an evidence_id the UI no longer shows as selected.
  const availableEvidenceIds = new Set(availableEvidence.map((item) => item.id));
  const evidenceIdsToSubmit = selectedEvidenceIds.filter((id) =>
    availableEvidenceIds.has(id)
  );

  const createMutation = useMutation({
    mutationFn: () =>
      createClaim({
        project_id: projectId,
        claim_no: form.claim_no || null,
        governing_clause: form.governing_clause || null,
        claim_basis: form.claim_basis || null,
        claim_type: form.claim_type,
        claiming_party: form.claiming_party,
        title: form.title,
        description: form.description || null,
        awareness_date: form.awareness_date,
        claimed_days: form.claimed_days === "" ? null : Number(form.claimed_days),
        claimed_cost_amount:
          form.claimed_cost_amount === "" ? null : Number(form.claimed_cost_amount),
        event_ids: selectedEventIds,
        daily_log_ids: selectedDailyLogIds,
        evidence_ids: evidenceIdsToSubmit,
      }),
    onSuccess: (claim) => navigate(`/projects/${projectId}/claims/${claim.id}`),
  });

  function toggleId(list, setList, id) {
    setList(
      list.includes(id) ? list.filter((x) => x !== id) : [...list, id]
    );
  }

  function handleSubmit(e) {
    e.preventDefault();
    createMutation.mutate();
  }

  return (
    <Stack spacing={2} sx={{ maxWidth: 720 }}>
      <Button
        component={RouterLink}
        to={`/projects/${projectId}/claims`}
        size="small"
        startIcon={<ArrowBackIcon fontSize="small" />}
        sx={{ alignSelf: "flex-start" }}
      >
        Back to claims
      </Button>

      <Typography variant="h4" fontWeight={700}>
        New Claim
      </Typography>

      <Paper sx={{ p: 3 }} component="form" onSubmit={handleSubmit}>
        <Stack spacing={2}>
          <TextField
            label="Claim No."
            value={form.claim_no}
            onChange={(e) => setForm({ ...form, claim_no: e.target.value })}
            helperText="Leave blank to auto-number (CLM-001, CLM-002, ...) or enter your own reference"
          />

          <TextField
            select
            label="Applicable governing clause"
            value={clauseSelection}
            onChange={(e) => handleClauseChange(e.target.value)}
            helperText="Selecting a ground auto-fills the governing clause below with the matching FIDIC Red Book 2017 Sub-Clause. Pick 'Other / type manually' if this claim's ground isn't in the list."
          >
            <MenuItem value="">— Select a claim ground —</MenuItem>
            {clauseOptions.map((option) => (
              <MenuItem key={option.event_type} value={option.event_type}>
                {option.event_type} ({option.clause_code})
              </MenuItem>
            ))}
            <MenuItem value={OTHER_CLAUSE_VALUE}>Other / type manually</MenuItem>
          </TextField>

          {selectedClauseOption && (
            <Alert severity="info">
              <strong>{selectedClauseOption.clause_code}</strong> —{" "}
              {selectedClauseOption.clause_title}
              <br />
              Entitlement: {selectedClauseOption.basis}
              <br />
              {selectedClauseOption.summary}
            </Alert>
          )}

          <TextField
            label="Governing clause"
            value={form.governing_clause}
            onChange={(e) => setForm({ ...form, governing_clause: e.target.value })}
            helperText="The substantive entitlement clause this claim is based on - auto-filled from the dropdown above, editable since Particular Conditions/MDB amendments can change clause numbers. Separate from the Sub-Clause 20.2 claims procedure this page already tracks."
          />

          <TextField
            select
            label="Claim type"
            value={form.claim_type}
            onChange={(e) => setForm({ ...form, claim_type: e.target.value })}
          >
            {CLAIM_TYPES.map((t) => (
              <MenuItem key={t} value={t}>
                {t}
              </MenuItem>
            ))}
          </TextField>

          <TextField
            select
            label="Claiming party"
            value={form.claiming_party}
            onChange={(e) => setForm({ ...form, claiming_party: e.target.value })}
          >
            {CLAIMING_PARTIES.map((p) => (
              <MenuItem key={p} value={p}>
                {p}
              </MenuItem>
            ))}
          </TextField>

          <TextField
            label="Title"
            required
            value={form.title}
            onChange={(e) => setForm({ ...form, title: e.target.value })}
          />

          <TextField
            label="Description"
            multiline
            minRows={2}
            value={form.description}
            onChange={(e) => setForm({ ...form, description: e.target.value })}
          />

          <TextField
            label="Awareness date"
            type="date"
            required
            slotProps={{ inputLabel: { shrink: true } }}
            helperText="Sub-Clause 20.2.1: the date the claiming party became aware, or should have become aware, of the event or circumstance - this is what the 28/84-day clocks run from."
            value={form.awareness_date}
            onChange={(e) => setForm({ ...form, awareness_date: e.target.value })}
          />

          <TextField
            label="Contractor's day-count ask (optional)"
            type="number"
            value={form.claimed_days}
            onChange={(e) => setForm({ ...form, claimed_days: e.target.value })}
          />

          <TextField
            label="Contractor's cost ask (optional)"
            type="number"
            value={form.claimed_cost_amount}
            onChange={(e) => setForm({ ...form, claimed_cost_amount: e.target.value })}
          />

          <Typography variant="subtitle2">Link supporting events</Typography>
          {eventsQuery.isLoading && <CircularProgress size={20} />}
          {eventsQuery.data && eventsQuery.data.length === 0 && (
            <Typography variant="body2" color="text.secondary">
              No events logged for this project yet.
            </Typography>
          )}
          {eventsQuery.data && eventsQuery.data.length > 0 && (
            <FormGroup>
              {eventsQuery.data.map((event) => (
                <FormControlLabel
                  key={event.id}
                  control={
                    <Checkbox
                      checked={selectedEventIds.includes(event.id)}
                      onChange={() =>
                        toggleId(selectedEventIds, setSelectedEventIds, event.id)
                      }
                    />
                  }
                  label={`${event.event_no ? `${event.event_no} — ` : ""}${event.event_date} — ${event.title}`}
                />
              ))}
            </FormGroup>
          )}

          <Typography variant="subtitle2">Link relevant Daily Log entries</Typography>
          {dailyLogsQuery.isLoading && <CircularProgress size={20} />}
          {dailyLogsQuery.data && dailyLogsQuery.data.length === 0 && (
            <Typography variant="body2" color="text.secondary">
              No Daily Log entries for this project yet.
            </Typography>
          )}
          {dailyLogsQuery.data && dailyLogsQuery.data.length > 0 && (
            <FormGroup>
              {dailyLogsQuery.data.map((log) => (
                <FormControlLabel
                  key={log.id}
                  control={
                    <Checkbox
                      checked={selectedDailyLogIds.includes(log.id)}
                      onChange={() =>
                        toggleId(selectedDailyLogIds, setSelectedDailyLogIds, log.id)
                      }
                    />
                  }
                  label={log.diary_date}
                />
              ))}
            </FormGroup>
          )}

          <Typography variant="subtitle2">Link evidence</Typography>
          {availableEvidence.length === 0 ? (
            <Typography variant="body2" color="text.secondary">
              Select an event or Daily Log above to see its attached evidence here.
            </Typography>
          ) : (
            <FormGroup>
              {availableEvidence.map((item) => (
                <FormControlLabel
                  key={item.id}
                  control={
                    <Checkbox
                      checked={selectedEvidenceIds.includes(item.id)}
                      onChange={() =>
                        toggleId(selectedEvidenceIds, setSelectedEvidenceIds, item.id)
                      }
                    />
                  }
                  label={item.filename || item.caption || `File ${item.id}`}
                />
              ))}
            </FormGroup>
          )}

          {createMutation.isError && (
            <Alert severity="error">{createMutation.error.message}</Alert>
          )}

          <Button type="submit" variant="contained" disabled={createMutation.isPending}>
            {createMutation.isPending ? "Creating..." : "Create Claim"}
          </Button>
        </Stack>
      </Paper>
    </Stack>
  );
}

export default NewClaimPage;
