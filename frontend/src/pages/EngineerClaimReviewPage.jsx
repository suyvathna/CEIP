import { useState } from "react";
import { useParams } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import Typography from "@mui/material/Typography";
import Stack from "@mui/material/Stack";
import Paper from "@mui/material/Paper";
import Button from "@mui/material/Button";
import Chip from "@mui/material/Chip";
import TextField from "@mui/material/TextField";
import MenuItem from "@mui/material/MenuItem";
import CircularProgress from "@mui/material/CircularProgress";
import Alert from "@mui/material/Alert";
import List from "@mui/material/List";
import ListItem from "@mui/material/ListItem";
import Container from "@mui/material/Container";
import {
  getPublicClaimOverview,
  respondToPublicFact,
  submitPublicEngineerResponse,
} from "../api/claimAccess";

/**
 * The Engineer's no-account-needed entry point into a single claim - a
 * magic link generated from the Contractor's claim detail screen. This
 * route sits outside the authenticated app shell entirely (no login, no
 * token in localStorage required).
 */
function EngineerClaimReviewPage() {
  const { token } = useParams();
  const queryClient = useQueryClient();

  const overviewQuery = useQuery({
    queryKey: ["publicClaimOverview", token],
    queryFn: () => getPublicClaimOverview(token),
    retry: false,
  });

  const [responseType, setResponseType] = useState("Agreement");
  const [responseDate, setResponseDate] = useState("");
  const [daysGranted, setDaysGranted] = useState("");
  const [comment, setComment] = useState("");

  function refresh() {
    queryClient.invalidateQueries({ queryKey: ["publicClaimOverview", token] });
  }

  const factMutation = useMutation({
    mutationFn: ({ factId, status, comment: c }) =>
      respondToPublicFact(token, factId, { status, response_comment: c }),
    onSuccess: refresh,
  });

  const responseMutation = useMutation({
    mutationFn: () =>
      submitPublicEngineerResponse(token, {
        response_type: responseType,
        response_date: responseDate,
        days_granted: daysGranted === "" ? null : Number(daysGranted),
        comment: comment || null,
      }),
    onSuccess: refresh,
  });

  if (overviewQuery.isLoading) {
    return (
      <Container maxWidth="md" sx={{ py: 4 }}>
        <CircularProgress />
      </Container>
    );
  }

  if (overviewQuery.isError) {
    return (
      <Container maxWidth="md" sx={{ py: 4 }}>
        <Alert severity="error">
          {overviewQuery.error.message ||
            "This link is invalid or has expired. Ask the Contractor for a new one."}
        </Alert>
      </Container>
    );
  }

  const { claim, project_name, clock, events, facts, fact_summary } = overviewQuery.data;

  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Stack spacing={2}>
        <Typography variant="overline" color="text.secondary">
          Claim review — {project_name}
        </Typography>
        <Stack direction="row" spacing={1} sx={{ alignItems: "center" }}>
          <Typography variant="h4" fontWeight={700}>
            {claim.title}
          </Typography>
          <Chip label={claim.status} />
        </Stack>
        {claim.description && (
          <Typography color="text.secondary">{claim.description}</Typography>
        )}

        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            Deadline clock
          </Typography>
          <Stack spacing={1}>
            {clock.stages.map((stage) => (
              <Stack key={stage.stage} direction="row" spacing={2} sx={{ flexWrap: "wrap" }}>
                <Chip size="small" label={stage.status.replace("_", " ")} />
                <Typography variant="body2" sx={{ flex: 1, minWidth: 240 }}>
                  {stage.label}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Deadline: {stage.deadline}
                </Typography>
              </Stack>
            ))}
          </Stack>
        </Paper>

        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            Supporting events
          </Typography>
          <List dense disablePadding>
            {events.map((event) => (
              <ListItem key={event.id} disableGutters>
                {event.event_date} — {event.title}
              </ListItem>
            ))}
          </List>
        </Paper>

        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            Fact-agreement register
          </Typography>
          {fact_summary && (
            <Stack direction="row" spacing={3} sx={{ mb: 2, flexWrap: "wrap" }}>
              <Typography variant="body2">
                <strong>{fact_summary.agreed_days_total}</strong> agreed days
              </Typography>
              <Typography variant="body2">
                Contractor's ask: <strong>{fact_summary.claimed_days ?? "—"}</strong>
              </Typography>
            </Stack>
          )}
          <Stack spacing={2}>
            {facts.map((fact) => (
              <Stack key={fact.id} spacing={1}>
                <Stack direction="row" spacing={1} sx={{ alignItems: "center" }}>
                  <Chip
                    size="small"
                    label={fact.status}
                    color={
                      fact.status === "Agreed"
                        ? "success"
                        : fact.status === "Disputed"
                        ? "error"
                        : "default"
                    }
                  />
                  <Typography variant="body2">
                    {fact.description}
                    {fact.agreed_days != null ? ` (${fact.agreed_days} days)` : ""}
                  </Typography>
                </Stack>
                {fact.status === "Proposed" && (
                  <Stack direction="row" spacing={1}>
                    <Button
                      size="small"
                      color="success"
                      onClick={() =>
                        factMutation.mutate({
                          factId: fact.id,
                          status: "Agreed",
                          comment: "Agreed via magic link",
                        })
                      }
                    >
                      Agree
                    </Button>
                    <Button
                      size="small"
                      color="error"
                      onClick={() =>
                        factMutation.mutate({
                          factId: fact.id,
                          status: "Disputed",
                          comment: "Disputed via magic link",
                        })
                      }
                    >
                      Dispute
                    </Button>
                    <Button
                      size="small"
                      onClick={() =>
                        factMutation.mutate({
                          factId: fact.id,
                          status: "NeedsEvidence",
                          comment: "Requesting more evidence",
                        })
                      }
                    >
                      Request evidence
                    </Button>
                  </Stack>
                )}
              </Stack>
            ))}
          </Stack>
        </Paper>

        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            Submit overall response (Sub-Clause 20.2.5)
          </Typography>
          <Stack direction="row" spacing={1} sx={{ flexWrap: "wrap" }}>
            <TextField
              select
              size="small"
              label="Response"
              value={responseType}
              onChange={(e) => setResponseType(e.target.value)}
            >
              {["Agreement", "PartialAgreement", "Disagreement", "Determination"].map(
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
              label="Date"
              slotProps={{ inputLabel: { shrink: true } }}
              value={responseDate}
              onChange={(e) => setResponseDate(e.target.value)}
            />
            <TextField
              type="number"
              size="small"
              label="Days granted"
              value={daysGranted}
              onChange={(e) => setDaysGranted(e.target.value)}
            />
          </Stack>
          <TextField
            size="small"
            fullWidth
            label="Comment"
            multiline
            minRows={2}
            sx={{ mt: 2 }}
            value={comment}
            onChange={(e) => setComment(e.target.value)}
          />
          <Button
            variant="contained"
            sx={{ mt: 2 }}
            disabled={!responseDate || responseMutation.isPending}
            onClick={() => responseMutation.mutate()}
          >
            Submit response
          </Button>
          {responseMutation.isSuccess && (
            <Alert severity="success" sx={{ mt: 2 }}>
              Response recorded.
            </Alert>
          )}
        </Paper>
      </Stack>
    </Container>
  );
}

export default EngineerClaimReviewPage;
