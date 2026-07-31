import { useState } from "react";
import { useParams, useNavigate, Link as RouterLink } from "react-router-dom";
import { useQuery, useMutation } from "@tanstack/react-query";
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
import { createClaim } from "../api/claims";

const CLAIM_TYPES = ["EOT", "Cost", "EOT+Cost"];
const CLAIMING_PARTIES = ["Contractor", "Employer"];

function NewClaimPage() {
  const { projectId } = useParams();
  const navigate = useNavigate();

  const eventsQuery = useQuery({
    queryKey: ["projectEvents", projectId],
    queryFn: () => getProjectEvents(projectId),
  });

  const [form, setForm] = useState({
    claim_no: "",
    governing_clause: "",
    claim_type: "EOT",
    claiming_party: "Contractor",
    title: "",
    description: "",
    awareness_date: "",
    claimed_days: "",
  });
  const [selectedEventIds, setSelectedEventIds] = useState([]);

  const createMutation = useMutation({
    mutationFn: () =>
      createClaim({
        project_id: projectId,
        claim_no: form.claim_no || null,
        governing_clause: form.governing_clause || null,
        claim_type: form.claim_type,
        claiming_party: form.claiming_party,
        title: form.title,
        description: form.description || null,
        awareness_date: form.awareness_date,
        claimed_days: form.claimed_days === "" ? null : Number(form.claimed_days),
        event_ids: selectedEventIds,
      }),
    onSuccess: (claim) => navigate(`/projects/${projectId}/claims/${claim.id}`),
  });

  function toggleEvent(eventId) {
    setSelectedEventIds((prev) =>
      prev.includes(eventId)
        ? prev.filter((id) => id !== eventId)
        : [...prev, eventId]
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
            label="Governing clause"
            value={form.governing_clause}
            onChange={(e) => setForm({ ...form, governing_clause: e.target.value })}
            helperText="The substantive entitlement clause this claim is based on, e.g. Sub-Clause 8.5(c) - Adverse Climatic Conditions, or Sub-Clause 13.1 - Variation. Separate from the Sub-Clause 20.2 claims procedure this page already tracks."
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
                      onChange={() => toggleEvent(event.id)}
                    />
                  }
                  label={`${event.event_date} — ${event.title}`}
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
