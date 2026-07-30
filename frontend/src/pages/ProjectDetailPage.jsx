import { useParams, useNavigate, Link as RouterLink } from "react-router-dom";
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
import EditIcon from "@mui/icons-material/Edit";
import DeleteIcon from "@mui/icons-material/Delete";
import AddIcon from "@mui/icons-material/Add";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import { getProject, deleteProject } from "../api/projects";
import { getProjectEvents } from "../api/events";
import EventList from "../components/EventList";
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

function ProjectDetailPage() {
  const { projectId } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { enqueueSnackbar } = useSnackbar();

  const projectQuery = useQuery({
    queryKey: ["project", projectId],
    queryFn: () => getProject(projectId),
  });

  const eventsQuery = useQuery({
    queryKey: ["projectEvents", projectId],
    queryFn: () => getProjectEvents(projectId),
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
        <Stack direction="row" spacing={2} sx={{ alignItems: "center" }}>
          <Typography variant="h4" fontWeight={700}>
            {project.project_name}
          </Typography>
          <Chip label={project.status} color={projectStatusColor(project.status)} />
        </Stack>
        <Stack direction="row" spacing={1}>
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
          <Grid size={{ xs: 6, sm: 4, md: 3 }}>
            <InfoField label="Planned start" value={project.planned_start} />
          </Grid>
          <Grid size={{ xs: 6, sm: 4, md: 3 }}>
            <InfoField label="Planned finish" value={project.planned_finish} />
          </Grid>
        </Grid>
      </Paper>

      <Stack
        direction="row"
        sx={{ justifyContent: "space-between", alignItems: "center" }}
      >
        <Typography variant="h6">Events</Typography>
        <Button
          component={RouterLink}
          to={`/projects/${projectId}/events/new`}
          startIcon={<AddIcon fontSize="small" />}
          variant="contained"
        >
          New Event
        </Button>
      </Stack>

      {eventsQuery.isLoading && <CircularProgress size={24} />}
      {eventsQuery.isError && (
        <Alert severity="error">{eventsQuery.error.message}</Alert>
      )}
      {eventsQuery.data && (
        <EventList projectId={projectId} events={eventsQuery.data} />
      )}
    </Stack>
  );
}

export default ProjectDetailPage;
