import { useQuery } from "@tanstack/react-query";
import { Link as RouterLink } from "react-router-dom";
import Typography from "@mui/material/Typography";
import Stack from "@mui/material/Stack";
import Paper from "@mui/material/Paper";
import Chip from "@mui/material/Chip";
import List from "@mui/material/List";
import ListItemButton from "@mui/material/ListItemButton";
import ListItemText from "@mui/material/ListItemText";
import CircularProgress from "@mui/material/CircularProgress";
import Alert from "@mui/material/Alert";
import { getAllEvents } from "../api/events";
import { getProjects } from "../api/projects";
import { getProjectClaims, getClaimClock } from "../api/claims";

const NOTICE_STATUS_LABELS = {
  pending: "Notice period open",
  overdue: "Notice deadline missed",
};

function EventDeadlines({ projects }) {
  const eventsQuery = useQuery({
    queryKey: ["allEvents"],
    queryFn: getAllEvents,
  });

  if (eventsQuery.isLoading) return <CircularProgress size={20} />;
  if (eventsQuery.isError) return <Alert severity="error">{eventsQuery.error.message}</Alert>;

  const projectNames = Object.fromEntries(projects.map((p) => [p.id, p.project_name]));

  const needsAttention = eventsQuery.data
    .filter((event) => event.notice_given_date === null)
    .map((event) => ({ ...event, project_name: projectNames[event.project_id] || "Unknown project" }))
    .sort((a, b) => a.notice_days_remaining - b.notice_days_remaining);

  if (needsAttention.length === 0) {
    return (
      <Typography variant="body2" color="text.secondary">
        Nothing needs notice action right now.
      </Typography>
    );
  }

  return (
    <List disablePadding>
      {needsAttention.map((event) => (
        <ListItemButton
          key={event.id}
          component={RouterLink}
          to={`/projects/${event.project_id}/events/${event.id}`}
          divider
        >
          <ListItemText
            primary={
              <Stack direction="row" spacing={1} sx={{ alignItems: "center" }}>
                <Chip
                  size="small"
                  color={event.notice_status === "overdue" ? "error" : "info"}
                  label={NOTICE_STATUS_LABELS[event.notice_status]}
                />
                <Typography variant="body1" fontWeight={600}>
                  {event.title}
                </Typography>
              </Stack>
            }
            secondary={`${event.project_name} — ${event.event_date} — deadline ${event.notice_deadline} — ${
              event.notice_status === "overdue"
                ? `${Math.abs(event.notice_days_remaining)} day(s) overdue`
                : `${event.notice_days_remaining} day(s) left`
            }`}
          />
        </ListItemButton>
      ))}
    </List>
  );
}

function ClaimDeadlines({ projects }) {
  const claimsQuery = useQuery({
    queryKey: ["allClaimsForDeadlines", projects.map((p) => p.id)],
    queryFn: async () => {
      const perProject = await Promise.all(
        projects.map(async (project) => {
          const claims = await getProjectClaims(project.id);
          const withClocks = await Promise.all(
            claims.map(async (claim) => ({
              claim,
              project,
              clock: await getClaimClock(claim.id),
            }))
          );
          return withClocks;
        })
      );
      return perProject.flat();
    },
    enabled: projects.length > 0,
  });

  if (claimsQuery.isLoading) return <CircularProgress size={20} />;
  if (claimsQuery.isError) return <Alert severity="error">{claimsQuery.error.message}</Alert>;

  const atRisk = (claimsQuery.data || [])
    .filter((item) => item.clock.at_risk)
    .sort((a, b) => (a.clock.days_remaining ?? 0) - (b.clock.days_remaining ?? 0));

  if (atRisk.length === 0) {
    return (
      <Typography variant="body2" color="text.secondary">
        No claims within 7 days of their next Sub-Clause 20.2 deadline right now.
      </Typography>
    );
  }

  return (
    <List disablePadding>
      {atRisk.map(({ claim, project, clock }) => (
        <ListItemButton
          key={claim.id}
          component={RouterLink}
          to={`/projects/${project.id}/claims/${claim.id}`}
          divider
        >
          <ListItemText
            primary={
              <Stack direction="row" spacing={1} sx={{ alignItems: "center" }}>
                <Chip
                  size="small"
                  color={clock.days_remaining < 0 ? "error" : "warning"}
                  label={clock.next_action?.label}
                />
                <Typography variant="body1" fontWeight={600}>
                  {claim.title}
                </Typography>
              </Stack>
            }
            secondary={`${project.project_name} — deadline ${clock.next_action?.deadline} — ${
              clock.days_remaining < 0
                ? `${Math.abs(clock.days_remaining)} day(s) overdue`
                : `${clock.days_remaining} day(s) left`
            }`}
          />
        </ListItemButton>
      ))}
    </List>
  );
}

function DeadlinesDashboardPage() {
  const projectsQuery = useQuery({
    queryKey: ["projects"],
    queryFn: getProjects,
  });

  if (projectsQuery.isLoading) return <CircularProgress />;
  if (projectsQuery.isError) return <Alert severity="error">{projectsQuery.error.message}</Alert>;

  return (
    <Stack spacing={3}>
      <Typography variant="h4" fontWeight={700}>
        Deadlines
      </Typography>

      <Paper sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom>
          Claims at risk (within 7 days, or overdue)
        </Typography>
        <ClaimDeadlines projects={projectsQuery.data} />
      </Paper>

      <Paper sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom>
          Event Notice Deadlines (Sub-Clause 20.2.1)
        </Typography>
        <EventDeadlines projects={projectsQuery.data} />
      </Paper>
    </Stack>
  );
}

export default DeadlinesDashboardPage;
