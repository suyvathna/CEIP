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
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import { getProject, deleteProject, updateProjectStatus } from "../api/projects";
import { getDeadlineFeed } from "../api/compliance";
import ProjectNav from "../components/ProjectNav";
import { projectStatusColor } from "../theme";

function InfoField({ label, value, mono }) {
  return (
    <div>
      <Typography
        variant="caption"
        color="text.secondary"
        sx={{ textTransform: "uppercase", letterSpacing: "0.06em", fontSize: "0.68rem", fontWeight: 600 }}
      >
        {label}
      </Typography>
      <Typography variant="body1" fontFamily={mono ? "'IBM Plex Mono', monospace" : undefined}>
        {value || "—"}
      </Typography>
    </div>
  );
}

const ATTENTION_CATEGORY_LABELS = {
  Compliance: "Compliance",
  Claim: "Claim (20.2)",
  Determination: "Determination (3.7)",
  Variation: "Variation (13 / 3.5)",
  Event: "Event notice",
};

// The three nearest open deadlines for this project, surfaced above
// everything else - "needs attention" before "everything about this
// project", matching how a site engineer actually scans a register.
function AttentionRail({ projectId }) {
  const feedQuery = useQuery({
    queryKey: ["deadlineFeed", projectId, "attention"],
    queryFn: () => getDeadlineFeed({ projectId }),
  });

  if (feedQuery.isLoading || feedQuery.isError) return null;

  const items = feedQuery.data.items.slice(0, 3);
  if (items.length === 0) return null;

  return (
    <Stack spacing={1}>
      <Stack direction="row" sx={{ justifyContent: "space-between", alignItems: "baseline", flexWrap: "wrap", gap: 1 }}>
        <Typography variant="h6">Needs attention</Typography>
        <Stack direction="row" spacing={2} sx={{ fontFamily: "'IBM Plex Mono', monospace", fontSize: "0.78rem", color: "text.secondary" }}>
          <span><b style={{ color: "inherit", fontWeight: 500 }}>{feedQuery.data.total}</b> open</span>
          {feedQuery.data.overdue > 0 && <span style={{ color: "#a02b2b" }}>{feedQuery.data.overdue} overdue</span>}
          {feedQuery.data.critical > 0 && <span style={{ color: "#a02b2b" }}>{feedQuery.data.critical} critical</span>}
        </Stack>
      </Stack>
      <Grid container spacing={1.5}>
        {items.map((item) => {
          const isCritical = item.severity === "Critical";
          const isOverdue = item.days_remaining < 0;
          return (
            <Grid key={`${item.source_type}-${item.source_id}-${item.stage}`} size={{ xs: 12, sm: 6, md: 4 }}>
              <Paper
                component={RouterLink}
                to={item.link_path}
                sx={{
                  display: "block",
                  p: 1.75,
                  textDecoration: "none",
                  color: "inherit",
                  borderLeft: "3px solid",
                  borderLeftColor: isCritical ? "error.main" : isOverdue ? "error.main" : "warning.main",
                  "&:hover": { bgcolor: "action.hover" },
                }}
              >
                <Stack direction="row" spacing={1} sx={{ alignItems: "center", mb: 1 }}>
                  <Chip
                    size="small"
                    label={isOverdue ? `${Math.abs(item.days_remaining)}d overdue` : `${item.days_remaining}d left`}
                    sx={{
                      fontFamily: "'IBM Plex Mono', monospace",
                      fontWeight: 500,
                      bgcolor: isCritical || isOverdue ? "#f7e4e1" : "#f4e7cc",
                      color: isCritical || isOverdue ? "error.main" : "warning.main",
                    }}
                  />
                </Stack>
                <Typography variant="body2" fontWeight={500} sx={{ mb: 0.5 }}>
                  {item.title}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  {ATTENTION_CATEGORY_LABELS[item.category] || item.category} · due {item.deadline}
                </Typography>
              </Paper>
            </Grid>
          );
        })}
      </Grid>
    </Stack>
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

  const projectQuery = useQuery({
    queryKey: ["project", projectId],
    queryFn: () => getProject(projectId),
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

      {/* Title block - project identity, refs and key parties in one
          register-style header, modelled on an engineering drawing's
          title block rather than a generic page heading. */}
      <Paper>
        <Stack
          direction="row"
          sx={{
            justifyContent: "space-between",
            alignItems: "flex-start",
            flexWrap: "wrap",
            gap: 2,
            p: "22px 26px 18px",
            borderBottom: "1px solid",
            borderColor: "divider",
          }}
        >
          <div>
            <Typography variant="h4" sx={{ fontSize: { xs: "1.6rem", sm: "2.1rem" } }}>
              {project.project_name}
            </Typography>
            <Stack
              direction="row"
              spacing={2}
              sx={{ mt: 0.75, flexWrap: "wrap", fontFamily: "'IBM Plex Mono', monospace", fontSize: "0.78rem", color: "text.secondary" }}
            >
              <span>{project.project_code}</span>
              {project.contract_no && <span>{project.contract_no}</span>}
              <span>{project.contract_type}</span>
            </Stack>
          </div>
          <Stack direction="row" spacing={1} sx={{ alignItems: "center", flexWrap: "wrap" }}>
            <Chip label={project.status} color={projectStatusColor(project.status)} />
            {project.is_overdue && (
              <Chip
                color="error"
                variant="outlined"
                label={`${project.days_overdue} day${project.days_overdue === 1 ? "" : "s"} past planned completion`}
              />
            )}
            <ProjectStatusActions project={project} onChanged={refreshProject} />
            <Button
              component={RouterLink}
              to={`/projects/${projectId}/edit`}
              startIcon={<EditIcon fontSize="small" />}
              variant="outlined"
              size="small"
            >
              Edit
            </Button>
            <Button
              onClick={handleDelete}
              startIcon={<DeleteIcon fontSize="small" />}
              color="error"
              variant="outlined"
              size="small"
              disabled={deleteMutation.isPending}
            >
              Delete
            </Button>
          </Stack>
        </Stack>
        <Grid container>
          {[
            ["Client", project.client_name],
            ["Contractor", project.contractor_name],
            ["Engineer", project.engineer_name],
            ["Site", `${project.site_address ? project.site_address + ", " : ""}${project.city}, ${project.country}`],
          ].map(([label, value], i) => (
            <Grid
              key={label}
              size={{ xs: 6, md: 3 }}
              sx={{
                p: "14px 22px",
                borderRight: { md: i < 3 ? "1px solid" : "none" },
                borderColor: "divider",
              }}
            >
              <InfoField label={label} value={value} />
            </Grid>
          ))}
        </Grid>
      </Paper>

      <AttentionRail projectId={projectId} />

      <Paper sx={{ p: 3 }}>
        <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 2, textTransform: "uppercase", letterSpacing: "0.06em", fontSize: "0.78rem" }}>
          Contract data
        </Typography>
        <Grid container spacing={3}>
          <Grid size={{ xs: 6, sm: 3 }}>
            <InfoField label="Commencement date" value={project.planned_start} mono />
          </Grid>
          <Grid size={{ xs: 6, sm: 3 }}>
            <InfoField label="Time for Completion" value={`${project.duration_days} days`} mono />
          </Grid>
          <Grid size={{ xs: 6, sm: 3 }}>
            <InfoField label="Completion date" value={project.planned_finish} mono />
          </Grid>
          <Grid size={{ xs: 6, sm: 3 }}>
            <InfoField
              label="Contract value"
              value={formatMoney(project.contract_value, project.currency)}
              mono
            />
          </Grid>
        </Grid>
      </Paper>

    </Stack>
  );
}

export default ProjectDetailPage;
