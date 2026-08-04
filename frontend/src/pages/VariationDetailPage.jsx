import { useState } from "react";
import { useParams, Link as RouterLink } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Typography from "@mui/material/Typography";
import Stack from "@mui/material/Stack";
import Paper from "@mui/material/Paper";
import Button from "@mui/material/Button";
import Chip from "@mui/material/Chip";
import Alert from "@mui/material/Alert";
import TextField from "@mui/material/TextField";
import MenuItem from "@mui/material/MenuItem";
import CircularProgress from "@mui/material/CircularProgress";
import Divider from "@mui/material/Divider";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import ProjectNav from "../components/ProjectNav";
import ContractClock from "../components/ContractClock";
import { todayLocalISODate } from "../utils/date";
import {
  getVariation,
  giveVariationNotice,
  recordVariationValuation,
  submitVariationProposal,
} from "../api/variations";

const ORIGIN_LABELS = {
  EngineerInstruction: "Engineer's Instruction, issued as a Variation",
  RequestForProposal: "Engineer's request for a proposal (13.3.2)",
  ValueEngineering: "Contractor's proposal (13.2 Value Engineering)",
  UnlabelledInstruction: "Instruction that was NOT called a Variation",
  Constructive: "Constructive variation — no instruction issued",
};

function NoticePanel({ variation, projectId }) {
  const queryClient = useQueryClient();
  const [date, setDate] = useState(todayLocalISODate());
  const [reference, setReference] = useState("");
  const [error, setError] = useState(null);

  const mutation = useMutation({
    mutationFn: () =>
      giveVariationNotice(variation.id, {
        notice_given_date: date,
        notice_reference: reference || null,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["variation", variation.id] });
      queryClient.invalidateQueries({ queryKey: ["variations", projectId] });
      queryClient.invalidateQueries({ queryKey: ["notificationSummary"] });
    },
    onError: (e) => setError(e.message),
  });

  if (variation.notice_given_date) {
    return (
      <Alert severity="success">
        Sub-Clause 3.5 Notice recorded on {variation.notice_given_date}
        {variation.notice_reference ? ` (ref ${variation.notice_reference})` : ""}.
      </Alert>
    );
  }

  return (
    <Paper sx={{ p: 3 }}>
      <Typography variant="h6" gutterBottom>
        Give the Sub-Clause 3.5 Notice
      </Typography>

      <Typography variant="body2" color="text.secondary" gutterBottom>
        Put on record that the Contractor considers this instruction a
        Variation. Due immediately, and before any related work starts.
      </Typography>

      {error && <Alert severity="error" sx={{ my: 1 }}>{error}</Alert>}

      <Stack spacing={2} sx={{ mt: 2 }}>
        <TextField
          type="date"
          size="small"
          label="Date Notice given"
          value={date}
          onChange={(e) => setDate(e.target.value)}
          slotProps={{ inputLabel: { shrink: true } }}
        />
        <TextField
          size="small"
          label="Your letter / transmittal reference"
          value={reference}
          onChange={(e) => setReference(e.target.value)}
        />
        <Button
          variant="contained"
          onClick={() => mutation.mutate()}
          disabled={mutation.isPending}
        >
          Record Notice
        </Button>
      </Stack>
    </Paper>
  );
}

function ProposalPanel({ variation, projectId }) {
  const queryClient = useQueryClient();
  const [date, setDate] = useState(todayLocalISODate());
  const [days, setDays] = useState("");
  const [cost, setCost] = useState("");
  const [error, setError] = useState(null);

  const mutation = useMutation({
    mutationFn: () =>
      submitVariationProposal(variation.id, {
        proposal_submitted_date: date,
        quoted_days: days === "" ? null : Number(days),
        quoted_cost: cost === "" ? null : Number(cost),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["variation", variation.id] });
      queryClient.invalidateQueries({ queryKey: ["variations", projectId] });
    },
    onError: (e) => setError(e.message),
  });

  if (variation.proposal_submitted_date) {
    return (
      <Alert severity="success">
        Proposal submitted {variation.proposal_submitted_date}
        {variation.quoted_days !== null ? ` — ${variation.quoted_days} day(s)` : ""}
        {variation.quoted_cost !== null ? ` — ${variation.quoted_cost}` : ""}.
      </Alert>
    );
  }

  return (
    <Paper sx={{ p: 3 }}>
      <Typography variant="h6" gutterBottom>
        Submit the Sub-Clause 13.3 proposal
      </Typography>

      {error && <Alert severity="error" sx={{ my: 1 }}>{error}</Alert>}

      <Stack spacing={2} sx={{ mt: 2 }}>
        <TextField
          type="date"
          size="small"
          label="Date submitted"
          value={date}
          onChange={(e) => setDate(e.target.value)}
          slotProps={{ inputLabel: { shrink: true } }}
        />
        <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
          <TextField
            fullWidth
            size="small"
            type="number"
            label="Time quoted (days)"
            value={days}
            onChange={(e) => setDays(e.target.value)}
          />
          <TextField
            fullWidth
            size="small"
            type="number"
            label="Cost quoted"
            value={cost}
            onChange={(e) => setCost(e.target.value)}
          />
        </Stack>
        <Button
          variant="contained"
          onClick={() => mutation.mutate()}
          disabled={mutation.isPending}
        >
          Record proposal
        </Button>
      </Stack>
    </Paper>
  );
}

function ValuationPanel({ variation, projectId }) {
  const queryClient = useQueryClient();
  const [days, setDays] = useState(variation.agreed_days ?? "");
  const [cost, setCost] = useState(variation.agreed_cost ?? "");
  const [status, setStatus] = useState("Valued");
  const [error, setError] = useState(null);

  const mutation = useMutation({
    mutationFn: () =>
      recordVariationValuation(variation.id, {
        agreed_days: days === "" ? null : Number(days),
        agreed_cost: cost === "" ? null : Number(cost),
        status,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["variation", variation.id] });
      queryClient.invalidateQueries({ queryKey: ["variations", projectId] });
    },
    onError: (e) => setError(e.message),
  });

  return (
    <Paper sx={{ p: 3 }}>
      <Typography variant="h6" gutterBottom>
        Outcome
      </Typography>

      {error && <Alert severity="error" sx={{ my: 1 }}>{error}</Alert>}

      <Stack spacing={2} sx={{ mt: 2 }}>
        <TextField
          select
          size="small"
          label="Outcome"
          value={status}
          onChange={(e) => setStatus(e.target.value)}
        >
          <MenuItem value="Valued">Agreed and valued</MenuItem>
          <MenuItem value="Instructed">Instructed as a Variation</MenuItem>
          <MenuItem value="Disputed">
            Engineer refused to treat it as a Variation
          </MenuItem>
          <MenuItem value="Rejected">Rejected</MenuItem>
          <MenuItem value="Withdrawn">Withdrawn</MenuItem>
        </TextField>

        {status === "Disputed" && (
          <Alert severity="warning">
            A refusal doesn&apos;t end this — it becomes a Sub-Clause 20.2
            claim, and the 28-day notice clock runs from the date the
            Contractor became aware of the refusal. Raise the claim from
            the Claims tab and link it here.
          </Alert>
        )}

        <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
          <TextField
            fullWidth
            size="small"
            type="number"
            label="Days agreed"
            value={days}
            onChange={(e) => setDays(e.target.value)}
          />
          <TextField
            fullWidth
            size="small"
            type="number"
            label="Cost agreed"
            value={cost}
            onChange={(e) => setCost(e.target.value)}
          />
        </Stack>

        <Button
          variant="contained"
          onClick={() => mutation.mutate()}
          disabled={mutation.isPending}
        >
          Record outcome
        </Button>
      </Stack>
    </Paper>
  );
}

function VariationDetailPage() {
  const { projectId, variationId } = useParams();

  const detailQuery = useQuery({
    queryKey: ["variation", variationId],
    queryFn: () => getVariation(variationId),
  });

  if (detailQuery.isLoading) return <CircularProgress />;
  if (detailQuery.isError)
    return <Alert severity="error">{detailQuery.error.message}</Alert>;

  const { variation, clock } = detailQuery.data;
  const needsNotice =
    !variation.is_labelled_as_variation && !variation.notice_given_date;

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

      <Stack direction="row" spacing={1} sx={{ alignItems: "center", flexWrap: "wrap" }}>
        {variation.variation_no && (
          <Chip variant="outlined" color="primary" label={variation.variation_no} />
        )}
        <Typography variant="h4" fontWeight={700}>
          {variation.title}
        </Typography>
      </Stack>

      <Typography variant="body2" color="text.secondary">
        {ORIGIN_LABELS[variation.origin] || variation.origin}
        {variation.instruction_reference
          ? ` — ref ${variation.instruction_reference}`
          : ""}
      </Typography>

      {needsNotice && (
        <Alert severity="error">
          <Typography variant="body2" fontWeight={600}>
            This instruction was not issued as a Variation and no
            Sub-Clause 3.5 Notice has been recorded.
          </Typography>
          <Typography variant="body2">
            The Notice is due immediately and before any related work
            begins. Once the work has started, the argument that this was a
            Variation is very much harder to run.
          </Typography>
        </Alert>
      )}

      <ContractClock
        clock={clock}
        title="Sub-Clause 3.5 / 13.3 clock"
        emptyText="No instruction date recorded, so no clock is running. Add the date the instruction was received to start it."
      />

      {variation.description && (
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            Description
          </Typography>
          <Typography variant="body2" sx={{ whiteSpace: "pre-wrap" }}>
            {variation.description}
          </Typography>
        </Paper>
      )}

      {!variation.is_labelled_as_variation && (
        <NoticePanel variation={variation} projectId={projectId} />
      )}

      <Divider />

      <ProposalPanel variation={variation} projectId={projectId} />

      <ValuationPanel variation={variation} projectId={projectId} />
    </Stack>
  );
}

export default VariationDetailPage;
