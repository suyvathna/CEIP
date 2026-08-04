import { useState } from "react";
import { useQueryClient, useMutation, useQuery } from "@tanstack/react-query";
import Typography from "@mui/material/Typography";
import Stack from "@mui/material/Stack";
import Paper from "@mui/material/Paper";
import Button from "@mui/material/Button";
import Chip from "@mui/material/Chip";
import Alert from "@mui/material/Alert";
import TextField from "@mui/material/TextField";
import MenuItem from "@mui/material/MenuItem";
import CircularProgress from "@mui/material/CircularProgress";
import ContractClock from "./ContractClock";
import { todayLocalISODate } from "../utils/date";
import {
  DETERMINATION_STATUS_COLORS,
  DETERMINATION_STATUS_LABELS,
} from "../utils/determination";
import {
  getClaimDetermination,
  giveNoticeOfDissatisfaction,
  recordDeterminationReceived,
} from "../api/determinations";

function ReceivedForm({ determination, onDone }) {
  const [noticeDate, setNoticeDate] = useState(todayLocalISODate());
  const [receivedDate, setReceivedDate] = useState(todayLocalISODate());
  const [outcome, setOutcome] = useState("PartiallyInFavour");
  const [days, setDays] = useState("");
  const [cost, setCost] = useState("");
  const [summary, setSummary] = useState("");
  const [error, setError] = useState(null);

  const mutation = useMutation({
    mutationFn: () =>
      recordDeterminationReceived(determination.id, {
        determination_notice_date: noticeDate,
        determination_received_date: receivedDate,
        determination_summary: summary || null,
        outcome,
        days_determined: days === "" ? null : Number(days),
        cost_determined: cost === "" ? null : Number(cost),
      }),
    onSuccess: onDone,
    onError: (e) => setError(e.message),
  });

  return (
    <Stack spacing={2} sx={{ mt: 2 }}>
      {error && <Alert severity="error">{error}</Alert>}

      <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
        <TextField
          fullWidth
          size="small"
          type="date"
          label="Date on the Engineer's Notice"
          value={noticeDate}
          onChange={(e) => setNoticeDate(e.target.value)}
          slotProps={{ inputLabel: { shrink: true } }}
        />
        <TextField
          fullWidth
          size="small"
          type="date"
          label="Date actually received"
          value={receivedDate}
          onChange={(e) => setReceivedDate(e.target.value)}
          slotProps={{ inputLabel: { shrink: true } }}
          helperText="The 28-day window runs from THIS date."
        />
      </Stack>

      {/* Worth the extra sentence: on Cambodian jobs a Notice dated the
          1st routinely reaches site on the 9th, and running the clock
          from the letter date silently costs eight of the twenty-eight
          days with no relief afterwards. */}
      {receivedDate !== noticeDate && (
        <Alert severity="info">
          The Notice of Dissatisfaction window runs from receipt, not from
          the date printed on the letter — so it closes {receivedDate}
          &nbsp;+ 28 days, not {noticeDate} + 28.
        </Alert>
      )}

      <TextField
        select
        size="small"
        label="Outcome"
        value={outcome}
        onChange={(e) => setOutcome(e.target.value)}
      >
        <MenuItem value="FullyInFavour">Fully in the Contractor&apos;s favour</MenuItem>
        <MenuItem value="PartiallyInFavour">Partially in favour</MenuItem>
        <MenuItem value="Rejected">Rejected</MenuItem>
      </TextField>

      <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
        <TextField
          fullWidth
          size="small"
          type="number"
          label="Days determined"
          value={days}
          onChange={(e) => setDays(e.target.value)}
        />
        <TextField
          fullWidth
          size="small"
          type="number"
          label="Cost determined"
          value={cost}
          onChange={(e) => setCost(e.target.value)}
        />
      </Stack>

      <TextField
        size="small"
        label="Summary of the determination"
        multiline
        minRows={2}
        value={summary}
        onChange={(e) => setSummary(e.target.value)}
      />

      <Button
        variant="contained"
        onClick={() => mutation.mutate()}
        disabled={mutation.isPending}
      >
        Record determination
      </Button>
    </Stack>
  );
}

function NodForm({ determination, onDone }) {
  const [date, setDate] = useState(todayLocalISODate());
  const [reference, setReference] = useState("");
  const [grounds, setGrounds] = useState("");
  const [error, setError] = useState(null);

  const mutation = useMutation({
    mutationFn: () =>
      giveNoticeOfDissatisfaction(determination.id, {
        nod_given_date: date,
        nod_reference: reference || null,
        nod_grounds: grounds || null,
      }),
    onSuccess: onDone,
    onError: (e) => setError(e.message),
  });

  return (
    <Stack spacing={2} sx={{ mt: 2 }}>
      {error && <Alert severity="error">{error}</Alert>}

      <TextField
        size="small"
        type="date"
        label="Date Notice of Dissatisfaction given"
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
      <TextField
        size="small"
        label="Grounds of dissatisfaction"
        multiline
        minRows={3}
        value={grounds}
        onChange={(e) => setGrounds(e.target.value)}
        helperText="State what is disputed and why. This is what a DAAB referral under Clause 21 is built from."
      />
      <Button
        variant="contained"
        color="error"
        onClick={() => mutation.mutate()}
        disabled={mutation.isPending}
      >
        Record Notice of Dissatisfaction
      </Button>
    </Stack>
  );
}

/**
 * The Sub-Clause 3.7 workflow, rendered from a determination detail
 * payload. Used both by the standalone determination screen and inline
 * on the claim detail page, so a Contractor sees the same NOD countdown
 * wherever they happen to be looking.
 */
export function DeterminationBody({ detail, onChanged }) {
  const { determination, clock } = detail;

  return (
    <Stack spacing={2}>
      <Stack direction="row" spacing={1} sx={{ alignItems: "center", flexWrap: "wrap" }}>
        {determination.determination_no && (
          <Chip variant="outlined" color="primary" label={determination.determination_no} />
        )}
        <Chip
          size="small"
          color={DETERMINATION_STATUS_COLORS[determination.status] || "default"}
          label={
            DETERMINATION_STATUS_LABELS[determination.status] ||
            determination.status
          }
        />
        {determination.subject_clause && (
          <Chip size="small" variant="outlined" label={determination.subject_clause} />
        )}
      </Stack>

      {determination.is_final_and_binding && (
        <Alert severity="error">
          <Typography variant="body2" fontWeight={600}>
            This determination became final and binding on{" "}
            {determination.became_final_on}.
          </Typography>
          <Typography variant="body2">
            The Notice of Dissatisfaction window closed with no Notice
            recorded. It can no longer be challenged — not before the DAAB,
            not in arbitration. Adjust the forecast to match.
          </Typography>
        </Alert>
      )}

      {determination.status === "DeemedRejection" && (
        <Alert severity="warning">
          The Engineer let the Sub-Clause 3.7.3 determination window lapse.
          Under FIDIC 2017 that is deemed a rejection, which opens the
          dispute route under Clause 21 — the Contractor is not obliged to
          keep waiting.
        </Alert>
      )}

      <ContractClock clock={clock} title="Sub-Clause 3.7 clock" />

      {determination.determination_summary && (
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            Engineer&apos;s determination
          </Typography>
          <Typography variant="body2" sx={{ whiteSpace: "pre-wrap" }}>
            {determination.determination_summary}
          </Typography>
          <Typography variant="caption" color="text.secondary">
            {determination.days_determined !== null
              ? `${determination.days_determined} day(s) determined. `
              : ""}
            {determination.cost_determined !== null
              ? `Cost determined: ${determination.cost_determined}.`
              : ""}
          </Typography>
        </Paper>
      )}

      {!determination.determination_received_date &&
        !determination.agreement_reached_date && (
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6">
              Record the Engineer&apos;s determination
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Two dates, and they are not interchangeable — see below.
            </Typography>
            <ReceivedForm determination={determination} onDone={onChanged} />
          </Paper>
        )}

      {determination.determination_received_date &&
        !determination.nod_given_date &&
        !determination.is_final_and_binding && (
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6">Notice of Dissatisfaction</Typography>
            <Typography variant="body2" color="text.secondary">
              If the determination is not accepted, this Notice must go in
              within the window above. Miss it and the determination is
              final and binding for good.
            </Typography>
            <NodForm determination={determination} onDone={onChanged} />
          </Paper>
        )}

      {determination.nod_given_date && (
        <Alert severity="success">
          Notice of Dissatisfaction recorded on {determination.nod_given_date}
          {determination.nod_reference ? ` (ref ${determination.nod_reference})` : ""}.
          The matter stays live and can be referred to the DAAB under
          Clause 21.
        </Alert>
      )}
    </Stack>
  );
}

/**
 * Claim-detail embed. Fetches the Sub-Clause 3.7 record attached to a
 * claim and renders nothing at all until one exists - a claim only gets
 * a determination once its fully detailed claim has gone in, and an
 * empty panel before then would just be noise on an already long page.
 */
function DeterminationPanel({ claimId, projectId }) {
  const queryClient = useQueryClient();

  const query = useQuery({
    queryKey: ["claimDetermination", claimId],
    queryFn: () => getClaimDetermination(claimId),
  });

  function handleChanged() {
    queryClient.invalidateQueries({ queryKey: ["claimDetermination", claimId] });
    queryClient.invalidateQueries({ queryKey: ["determinations", projectId] });
    queryClient.invalidateQueries({ queryKey: ["notificationSummary"] });
  }

  if (query.isLoading) return <CircularProgress size={20} />;
  if (query.isError) return <Alert severity="error">{query.error.message}</Alert>;
  if (!query.data) return null;

  return (
    <Paper sx={{ p: 3 }}>
      <Typography variant="h6" gutterBottom>
        Sub-Clause 3.7 — Agreement or Determination
      </Typography>
      <DeterminationBody detail={query.data} onChanged={handleChanged} />
    </Paper>
  );
}

export default DeterminationPanel;
