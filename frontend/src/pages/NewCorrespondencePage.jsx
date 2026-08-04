import { useState } from "react";
import { useNavigate, useParams, Link as RouterLink } from "react-router-dom";
import { useMutation } from "@tanstack/react-query";
import Typography from "@mui/material/Typography";
import Stack from "@mui/material/Stack";
import Paper from "@mui/material/Paper";
import Button from "@mui/material/Button";
import TextField from "@mui/material/TextField";
import MenuItem from "@mui/material/MenuItem";
import Alert from "@mui/material/Alert";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import ProjectNav from "../components/ProjectNav";
import { todayLocalISODate } from "../utils/date";
import { createCorrespondence } from "../api/correspondence";

const DIRECTIONS = [
  { value: "Outgoing", label: "Outgoing — Contractor to Engineer" },
  { value: "Incoming", label: "Incoming — Engineer to Contractor" },
];

const METHODS = ["Email", "Letter", "Fax", "Hand Delivery", "Site Memo", "Other"];

function NewCorrespondencePage() {
  const { projectId } = useParams();
  const navigate = useNavigate();

  const [form, setForm] = useState({
    direction: "Outgoing",
    correspondence_date: todayLocalISODate(),
    reference: "",
    subject: "",
    method: "Email",
    related_to: "",
    summary: "",
  });
  const [error, setError] = useState(null);

  const mutation = useMutation({
    mutationFn: (payload) => createCorrespondence(payload),
    onSuccess: (correspondence) =>
      navigate(`/projects/${projectId}/correspondence/${correspondence.id}`),
    onError: (e) => setError(e.message),
  });

  function setField(name, value) {
    setForm((current) => ({ ...current, [name]: value }));
  }

  function handleSubmit(event) {
    event.preventDefault();
    setError(null);

    mutation.mutate({
      project_id: projectId,
      direction: form.direction,
      correspondence_date: form.correspondence_date,
      reference: form.reference || null,
      subject: form.subject,
      method: form.method || null,
      related_to: form.related_to || null,
      summary: form.summary || null,
    });
  }

  return (
    <Stack spacing={2}>
      <Button
        component={RouterLink}
        to={`/projects/${projectId}/correspondence`}
        size="small"
        startIcon={<ArrowBackIcon fontSize="small" />}
        sx={{ alignSelf: "flex-start" }}
      >
        Back to correspondence
      </Button>

      <ProjectNav projectId={projectId} active="correspondence" />

      <Typography variant="h4" fontWeight={700}>
        Log correspondence
      </Typography>

      {error && <Alert severity="error">{error}</Alert>}

      <Paper sx={{ p: 3 }}>
        <Stack component="form" spacing={2} onSubmit={handleSubmit}>
          <TextField
            select
            required
            label="Direction"
            value={form.direction}
            onChange={(e) => setField("direction", e.target.value)}
          >
            {DIRECTIONS.map((option) => (
              <MenuItem key={option.value} value={option.value}>
                {option.label}
              </MenuItem>
            ))}
          </TextField>

          <TextField
            required
            label="Subject"
            value={form.subject}
            onChange={(e) => setField("subject", e.target.value)}
            placeholder="e.g. Notice of unforeseeable ground conditions at Ch. 3+200"
          />

          <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
            <TextField
              fullWidth
              required
              type="date"
              label="Date"
              value={form.correspondence_date}
              onChange={(e) => setField("correspondence_date", e.target.value)}
              slotProps={{ inputLabel: { shrink: true } }}
            />
            <TextField
              fullWidth
              select
              label="Method"
              value={form.method}
              onChange={(e) => setField("method", e.target.value)}
            >
              {METHODS.map((m) => (
                <MenuItem key={m} value={m}>
                  {m}
                </MenuItem>
              ))}
            </TextField>
          </Stack>

          <TextField
            label="Reference (letter / transmittal / email ref.)"
            value={form.reference}
            onChange={(e) => setField("reference", e.target.value)}
          />

          <TextField
            label="Related to (optional — e.g. VO-003, CLM-002, Sub-Clause 20.2.1 Notice)"
            value={form.related_to}
            onChange={(e) => setField("related_to", e.target.value)}
          />

          <TextField
            label="Summary"
            multiline
            minRows={3}
            value={form.summary}
            onChange={(e) => setField("summary", e.target.value)}
          />

          <Button
            type="submit"
            variant="contained"
            disabled={mutation.isPending || !form.subject || !form.correspondence_date}
          >
            Log it
          </Button>
        </Stack>
      </Paper>
    </Stack>
  );
}

export default NewCorrespondencePage;
