import { useState } from "react";
import { useParams, useNavigate, useSearchParams, Link as RouterLink } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useSnackbar } from "notistack";
import Typography from "@mui/material/Typography";
import Stack from "@mui/material/Stack";
import Paper from "@mui/material/Paper";
import Grid from "@mui/material/Grid";
import Button from "@mui/material/Button";
import Chip from "@mui/material/Chip";
import CircularProgress from "@mui/material/CircularProgress";
import Alert from "@mui/material/Alert";
import Tabs from "@mui/material/Tabs";
import Tab from "@mui/material/Tab";
import EditIcon from "@mui/icons-material/Edit";
import DeleteIcon from "@mui/icons-material/Delete";
import AddIcon from "@mui/icons-material/Add";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import { getProject, deleteProject, updateProjectStatus } from "../api/projects";
import { getProjectEvents } from "../api/events";
import { getProjectDailyLogs } from "../api/dailyLogs";
import EventList from "../components/EventList";
import DailyLogList from "../components/DailyLogList";
import ProjectNav from "../components/ProjectNav";
import { projectStatusColor } from "../theme";

function InfoField({ label, value }) {
  return (
    <div>
      <Typography variant="caption" color="text.secondary">
        {label}
      </Typography>
      <Typography variant="body1">{value || "—"}</Typography>
    </div>
  );
}

function formatMoney(value, currency) {
  if (value === null || value === undefined) return null;
  const amount = Number(value).toLocaleString(undefined, {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
  return `${currency || ""} ${amount}`.trim();
}

function ProjectStatusActions({ project, onChanged }) {
  const { enqueueSnackbar } = useSnackbar();

  const statusMutation = useMutation({
    mutationFn: (status) => updateProjectStatus(project.id, status),
    onSuccess: () => {
      enqueueSnackbar("Project status updated", { variant: "success" });
      onChanged();
    },
    onError: (err) => enqueueSnackbar(err.message, { variant: "error" }),
  });

  if (project.status === "Completed") {
    return (
      <Button
        size="small"
        variant="outlined"
        disabled={statusMutation.isPending}
        onClick={() => statusMutation.mutate("In Progress")}
      >
        Reopen project
      </Button>
    );
  }

  if (project.status === "On Hold") {
    return (
      <Button
        size="small"
        variant="outlined"
        disabled={statusMutation.isPending}
        onClick={() => statusMutation.mutate("In Progress")}
      >
        Resume project
      </Button>
    );
  }

  return (
    <Stack direction="row" spacing={1}>
      <Button
        size="small"
        variant="outlined"
        color="warning"
        disabled={statusMutation.isPending}
        onClick={() => statusMutation.mutate("On Hold")}
      >
        Put on hold
      </Button>
      <Button
        size="small"
        variant="outlined"
        color="success"
        disabled={statusMutation.isPending}
        onClick={() => statusMutation.mutate("Completed")}
      >
        Mark completed
      </Button>
    </Stack>
  );
}

function ProjectDetailPage() {
  const { projectId } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { enqueueSnackbar } = useSnackbar();
  const [searchParams, setSearchParams] = useSearchParams();
  // Landing here from a Report tab stat tile (e.g. "High Severity")
  // arrives with ?tab=events&severity=High - pick that up on first
  // render so the right tab and filter are already showing, instead of
  // making the Contractor navigate there by hand.
  const [activityTab, setActivityTab] = useState(
    () => searchParams.get("tab") || "events"
  );
  const severityFilter = searchParams.get("severity");
  const statusFilter = searchParams.get("status");
  const hasEventFilter = Boolean(severityFilter || statusFilter);

  const projectQuery = useQuery({
    queryKey: ["project", projectId],
    queryFn: () => getProject(projectId),
  });

  const eventsQuery = useQuery({
    queryKey: ["projectEvents", projectId],
    queryFn: () => getProjectEvents(projectId),
  });

  const dailyLogsQuery = useQuery({
    queryKey: ["projectDailyLogs", projectId],
    queryFn: () => getProjectDailyLogs(projectId),
  });

  const deleteMutation = useMutation({
    mutationFn: () => deleteProject(projectId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projects"] });
      navigate("/");
    },
    onError: (err) => enqueueSnackbar(err.message, { variant: "error" }),
  });

  function handleDelete() {
    if (
      !window.confirm(
        `Delete "${projectQuery.data?.project_name}"? This cannot be undone.`
      )
    ) {
      return;
    }
    deleteMutation.mutate();
  }

  function clearEventFilter() {
    const next = new URLSearchParams(searchParams);
    next.delete("severity");
    next.delete("status");
    setSearchParams(next);
  }

  function refreshProject() {
    queryClient.invalidateQueries({ queryKey: ["project", projectId] });
    queryClient.invalidateQueries({ queryKey: ["projects"] });
  }

  if (projectQuery.isLoading) {
    return <CircularProgress />;
  }

  if (projectQuery.isError) {
    return <Alert severity="error">{projectQuery.error.message}</Alert>;
  }

  const project = projectQuery.data;

  return (
    <Stack spacing={2}>
      <Button
        component={RouterLink}
        to="/"
        size="small"
        startIcon={<ArrowBackIcon fontSize="small" />}
        sx={{ alignSelf: "flex-start" }}
      >
        Back to projects
      </Button>

      <ProjectNav projectId={projectId} active="overview" />

      <Stack
        direction="row"
        sx={{
          justifyContent: "space-between",
          alignItems: "flex-start",
          flexWrap: "wrap",
          gap: 2,
        }}
      >
        <Stack direction="row" spacing={2} sx={{ alignItems: "center", flexWrap: "wrap" }}>
          <Typography variant="h4" fontWeight={700}>
            {project.project_name}
          </Typography>
          <Chip label={project.status} color={projectStatusColor(project.status)} />
          {project.is_overdue && (
            <Chip
              color="error"
              variant="outlined"
              label={`${project.days_overdue} day${project.days_overdue === 1 ? "" : "s"} past planned completion`}
            />
          )}
        </Stack>
        <Stack direction="row" spacing={1} sx={{ alignItems: "center", flexWrap: "wrap" }}>
          <ProjectStatusActions project={project} onChanged={refreshProject} />
          <Button
            component={RouterLink}
            to={`/projects/${projectId}/edit`}
            startIcon={<EditIcon fontSize="small" />}
            variant="outlined"
          >
            Edit
          </Button>
          <Button
            onClick={handleDelete}
            startIcon={<DeleteIcon fontSize="small" />}
            color="error"
            variant="outlined"
            disabled={deleteMutation.isPending}
          >
            Delete
          </Button>
        </Stack>
      </Stack>

      <Paper sx={{ p: 3 }}>
        <Grid container spacing={3}>
          <Grid size={{ xs: 6, sm: 4, md: 3 }}>
            <InfoField label="Project code" value={project.project_code} />
          </Grid>
          <Grid size={{ xs: 6, sm: 4, md: 3 }}>
            <InfoField label="Contract No." value={project.contract_no} />
          </Grid>
          <Grid size={{ xs: 6, sm: 4, md: 3 }}>
            <InfoField label="Client" value={project.client_name} />
          </Grid>
          <Grid size={{ xs: 6, sm: 4, md: 3 }}>
            <InfoField label="Contractor" value={project.contractor_name} />
          </Grid>
          <Grid size={{ xs: 6, sm: 4, md: 3 }}>
            <InfoField label="Engineer" value={project.engineer_name} />
          </Grid>
          <Grid size={{ xs: 6, sm: 4, md: 3 }}>
            <InfoField label="Contract type" value={project.contract_type} />
          </Grid>
          <Grid size={{ xs: 6, sm: 4, md: 3 }}>
            <InfoField
              label="Location"
              value={`${project.city}, ${project.country}`}
            />
          </Grid>
          <Grid size={{ xs: 12, sm: 8, md: 6 }}>
            <InfoField label="Site address" value={project.site_address} />
          </Grid>
          <Grid size={{ xs: 6, sm: 4, md: 3 }}>
            <InfoField label="Commencement date" value={project.planned_start} />
          </Grid>
          <Grid size={{ xs: 6, sm: 4, md: 3 }}>
            <InfoField label="Time for Completion" value={`${project.duration_days} days`} />
          </Grid>
          <Grid size={{ xs: 6, sm: 4, md: 3 }}>
            <InfoField label="Completion date" value={project.planned_finish} />
          </Grid>
          <Grid size={{ xs: 6, sm: 4, md: 3 }}>
            <InfoField
              label="Contract value"
              value={formatMoney(project.contract_value, project.currency)}
            />
          </Grid>
        </Grid>
      </Paper>

      <Stack
        direction="row"
        sx={{ justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 1 }}
      >
        <Tabs
          value={activityTab}
          onChange={(_, v) => {
            setActivityTab(v);
            const next = new URLSearchParams(searchParams);
            next.set("tab", v);
            setSearchParams(next);
          }}
        >
          <Tab value="events" label="Events" />
          <Tab value="dailyLog" label="Daily Log" />
        </Tabs>
        <Stack direction="row" spacing={1}>
          <Button
            component={RouterLink}
            to={`/projects/${projectId}/daily-log/new`}
            startIcon={<AddIcon fontSize="small" />}
            variant="outlined"
          >
            New Daily Log
          </Button>
          <Button
            component={RouterLink}
            to={`/projects/${projectId}/events/new`}
            startIcon={<AddIcon fontSize="small" />}
            variant="contained"
          >
            New Event
          </Button>
        </Stack>
      </Stack>

      {activityTab === "events" && (
        <>
          {hasEventFilter && (
            <Stack direction="row" spacing={1} sx={{ alignItems: "center" }}>
              {severityFilter && (
                <Chip size="small" label={`Severity: ${severityFilter}`} />
              )}
              {statusFilter && (
                <Chip size="small" label={`Status: ${statusFilter}`} />
              )}
              <Button size="small" onClick={clearEventFilter}>
                Clear filter
              </Button>
            </Stack>
          )}
          {eventsQuery.isLoading && <CircularProgress size={24} />}
          {eventsQuery.isError && (
            <Alert severity="error">{eventsQuery.error.message}</Alert>
          )}
          {eventsQuery.data && (
            <EventList
              projectId={projectId}
              events={eventsQuery.data.filter(
                (event) =>
                  (!severityFilter || event.severity === severityFilter) &&
                  (!statusFilter || event.status === statusFilter)
              )}
            />
          )}
        </>
      )}

      {activityTab === "dailyLog" && (
        <>
          {dailyLogsQuery.isLoading && <CircularProgress size={24} />}
          {dailyLogsQuery.isError && (
            <Alert severity="error">{dailyLogsQuery.error.message}</Alert>
          )}
          {dailyLogsQuery.data && (
            <DailyLogList projectId={projectId} dailyLogs={dailyLogsQuery.data} />
          )}
        </>
      )}
    </Stack>
  );
}

export default ProjectDetailPage;
