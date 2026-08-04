import { useState } from "react";
import { useNavigate, useParams, Link as RouterLink } from "react-router-dom";
import { useMutation, useQuery } from "@tanstack/react-query";
import Typography from "@mui/material/Typography";
import Stack from "@mui/material/Stack";
import Paper from "@mui/material/Paper";
import Button from "@mui/material/Button";
import TextField from "@mui/material/TextField";
import MenuItem from "@mui/material/MenuItem";
import Alert from "@mui/material/Alert";
import FormControlLabel from "@mui/material/FormControlLabel";
import Checkbox from "@mui/material/Checkbox";
import CircularProgress from "@mui/material/CircularProgress";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import ProjectNav from "../components/ProjectNav";
import { todayLocalISODate } from "../utils/date";
import { createVariation, getVariationOriginOptions } from "../api/variations";

function NewVariationPage() {
  const { projectId } = useParams();
  const navigate = useNavigate();

  const [form, setForm] = useState({
    title: "",
    description: "",
    origin: "",
    instruction_reference: "",
    instruction_date: todayLocalISODate(),
    instruction_received_date: todayLocalISODate(),
    work_commenced: false,
    work_commenced_date: "",
    proposal_requested_date: "",
  });
  const [error, setError] = useState(null);

  const optionsQuery = useQuery({
    queryKey: ["variationOrigins", projectId],
    queryFn: () => getVariationOriginOptions(projectId),
  });

  const mutation = useMutation({
    mutationFn: (payload) => createVariation(payload),
    onSuccess: (variation) =>
      navigate(`/projects/${projectId}/variations/${variation.id}`),
    onError: (e) => setError(e.message),
  });

  const options = optionsQuery.data?.options || [];
  const selected = options.find((option) => option.value === form.origin);

  function setField(name, value) {
    setForm((current) => ({ ...current, [name]: value }));
  }

  function handleSubmit(event) {
    event.preventDefault();
    setError(null);

    mutation.mutate({
      project_id: projectId,
      title: form.title,
      description: form.description || null,
      origin: form.origin,
      instruction_reference: form.instruction_reference || null,
      instruction_date: form.instruction_date || null,
      instruction_received_date: form.instruction_received_date || null,
      // The server forces this to match the origin anyway - the flag and
      // the origin are not allowed to disagree, since the whole
      // Sub-Clause 3.5 alarm hangs off them.
      is_labelled_as_variation: form.origin === "EngineerInstruction",
      work_commenced: form.work_commenced,
      work_commenced_date: form.work_commenced_date || null,
      proposal_requested_date: form.proposal_requested_date || null,
    });
  }

  return (
    <Stack spacing={2}>
      <Button
        component={RouterLink}
        to={`/projects/${projectId}/variations`}
        size="small"
        startIcon={<ArrowBackIcon fontSize="small" />}
        sx={{ alignSelf: "flex-start" }}
      >
        Back to variations
      </Button>

      <ProjectNav projectId={projectId} active="variations" />

      <Typography variant="h4" fontWeight={700}>
        Log an instruction or Variation
      </Typography>

      {optionsQuery.isLoading && <CircularProgress size={24} />}
      {error && <Alert severity="error">{error}</Alert>}

      <Paper sx={{ p: 3 }}>
        <Stack component="form" spacing={2} onSubmit={handleSubmit}>
          <TextField
            required
            label="Title"
            value={form.title}
            onChange={(e) => setField("title", e.target.value)}
            placeholder="e.g. Revised rebar detail to pile cap PC-12"
          />

          <TextField
            select
            required
            label="How did this change arrive?"
            value={form.origin}
            onChange={(e) => setField("origin", e.target.value)}
            helperText="This is the field that decides whether a Sub-Clause 3.5 notice clock starts."
          >
            {options.map((option) => (
              <MenuItem key={option.value} value={option.value}>
                {option.label}
              </MenuItem>
            ))}
          </TextField>

          {/* The single most useful thing this screen does: tell a site
              engineer, at the moment of logging, that the category they
              just picked carries an immediate notice requirement. */}
          {selected && (
            <Alert severity={selected.triggers_immediate_notice ? "error" : "info"}>
              {selected.description}
            </Alert>
          )}

          <TextField
            label="Description"
            multiline
            minRows={3}
            value={form.description}
            onChange={(e) => setField("description", e.target.value)}
          />

          <TextField
            label="Engineer's reference (letter / drawing rev / memo no.)"
            value={form.instruction_reference}
            onChange={(e) => setField("instruction_reference", e.target.value)}
          />

          <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
            <TextField
              fullWidth
              type="date"
              label="Date on the instruction"
              value={form.instruction_date}
              onChange={(e) => setField("instruction_date", e.target.value)}
              slotProps={{ inputLabel: { shrink: true } }}
            />
            <TextField
              fullWidth
              type="date"
              label="Date actually received"
              value={form.instruction_received_date}
              onChange={(e) =>
                setField("instruction_received_date", e.target.value)
              }
              slotProps={{ inputLabel: { shrink: true } }}
              helperText="The clock runs from receipt, not from the date printed on the letter."
            />
          </Stack>

          <FormControlLabel
            control={
              <Checkbox
                checked={form.work_commenced}
                onChange={(e) => setField("work_commenced", e.target.checked)}
              />
            }
            label="Work on this instruction has already started"
          />

          {form.work_commenced && (
            <>
              <TextField
                type="date"
                label="Date work commenced"
                value={form.work_commenced_date}
                onChange={(e) => setField("work_commenced_date", e.target.value)}
                slotProps={{ inputLabel: { shrink: true } }}
              />
              {selected?.triggers_immediate_notice && (
                <Alert severity="error">
                  Sub-Clause 3.5 required the Notice before this work began,
                  so it is already late. Give it immediately anyway and
                  record why it was delayed — a late Notice is worth
                  considerably more than none.
                </Alert>
              )}
            </>
          )}

          <TextField
            type="date"
            label="Date a proposal was requested (13.3.2, if any)"
            value={form.proposal_requested_date}
            onChange={(e) => setField("proposal_requested_date", e.target.value)}
            slotProps={{ inputLabel: { shrink: true } }}
          />

          {optionsQuery.data && (
            <Alert severity="info">{optionsQuery.data.disclaimer}</Alert>
          )}

          <Button
            type="submit"
            variant="contained"
            disabled={mutation.isPending || !form.title || !form.origin}
          >
            Log it
          </Button>
        </Stack>
      </Paper>
    </Stack>
  );
}

export default NewVariationPage;
