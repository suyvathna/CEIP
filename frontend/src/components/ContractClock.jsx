import Stack from "@mui/material/Stack";
import Paper from "@mui/material/Paper";
import Chip from "@mui/material/Chip";
import Alert from "@mui/material/Alert";
import Typography from "@mui/material/Typography";
import List from "@mui/material/List";
import ListItem from "@mui/material/ListItem";
import ListItemText from "@mui/material/ListItemText";

/**
 * Renders any of the platform's contractual clocks.
 *
 * All three lifecycles - Sub-Clause 20.2 claims, Sub-Clause 3.7
 * determinations and Sub-Clause 3.5 / 13.3 variations - are computed by
 * the same backend service and come back in the same shape (stages,
 * next_action, days_remaining, at_risk). One component renders all of
 * them, so the way a deadline looks doesn't depend on which screen you
 * happen to be on, and there is one place to change if the vocabulary
 * ever grows.
 */

const STATUS_COLORS = {
  met: "success",
  missed: "error",
  overdue: "error",
  pending: "info",
  window_closed: "default",
};

const STATUS_LABELS = {
  met: "Done in time",
  missed: "Done late — time-bar already applied",
  overdue: "Overdue",
  pending: "Open",
  window_closed: "Window closed",
};

function ContractClock({ clock, title = "Contractual clock", emptyText }) {
  if (!clock) return null;

  const { stages = [], next_action: next, days_remaining: daysRemaining } = clock;

  if (stages.length === 0) {
    return (
      <Paper sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom>
          {title}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          {emptyText || "No deadline is running on this record yet."}
        </Typography>
      </Paper>
    );
  }

  return (
    <Paper sx={{ p: 3 }}>
      <Typography variant="h6" gutterBottom>
        {title}
      </Typography>

      {next && (
        <Alert
          severity={
            daysRemaining < 0 ? "error" : clock.at_risk ? "warning" : "info"
          }
          sx={{ mb: 2 }}
        >
          <Typography variant="body2" fontWeight={600}>
            Next: {next.label}
          </Typography>
          <Typography variant="body2">
            Deadline {next.deadline} —{" "}
            {daysRemaining < 0
              ? `${Math.abs(daysRemaining)} day(s) overdue`
              : `${daysRemaining} day(s) left`}
          </Typography>
        </Alert>
      )}

      {/* The one thing the shared clock shape can't express: under
          Sub-Clause 3.5 the Notice was due before work started, so a
          Contractor who has already begun is out of time whatever the
          remaining-days arithmetic says. Saying "4 days left" there
          would be worse than saying nothing. */}
      {clock.notice_late_because_work_started && (
        <Alert severity="error" sx={{ mb: 2 }}>
          Work on this instruction started before the Sub-Clause 3.5 Notice
          was given. The Notice was required immediately and before any
          related work began, so it is already late regardless of the dates
          below. Give it anyway and record why it was delayed — a late
          Notice is worth considerably more than none.
        </Alert>
      )}

      <List disablePadding>
        {stages.map((stage) => (
          <ListItem key={stage.stage} divider disableGutters sx={{ py: 1 }}>
            <ListItemText
              primary={
                <Stack
                  direction="row"
                  spacing={1}
                  sx={{ alignItems: "center", flexWrap: "wrap" }}
                >
                  <Chip
                    size="small"
                    color={STATUS_COLORS[stage.status] || "default"}
                    label={STATUS_LABELS[stage.status] || stage.status}
                  />
                  <Typography variant="body2" fontWeight={600}>
                    {stage.label}
                  </Typography>
                </Stack>
              }
              secondary={`Deadline ${stage.deadline}${
                stage.completed_date ? ` — recorded ${stage.completed_date}` : ""
              }`}
            />
          </ListItem>
        ))}
      </List>
    </Paper>
  );
}

export default ContractClock;
