import { Link as RouterLink } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import Typography from "@mui/material/Typography";
import Stack from "@mui/material/Stack";
import Button from "@mui/material/Button";
import Grid from "@mui/material/Grid";
import CircularProgress from "@mui/material/CircularProgress";
import Alert from "@mui/material/Alert";
import AddIcon from "@mui/icons-material/Add";
import { getProjects } from "../api/projects";
import ProjectCard from "../components/ProjectCard";

function ProjectListPage() {
  const { data: projects, isLoading, isError, error } = useQuery({
    queryKey: ["projects"],
    queryFn: getProjects,
  });

  return (
    <Stack spacing={3}>
      <Stack
        direction="row"
        sx={{ justifyContent: "space-between", alignItems: "center" }}
      >
        <Typography variant="h4" fontWeight={700}>
          Projects
        </Typography>
        <Button
          component={RouterLink}
          to="/projects/new"
          variant="contained"
          startIcon={<AddIcon fontSize="small" />}
        >
          New Project
        </Button>
      </Stack>

      {isLoading && <CircularProgress />}
      {isError && <Alert severity="error">{error.message}</Alert>}
      {projects && projects.length === 0 && (
        <Typography color="text.secondary">No projects yet.</Typography>
      )}

      <Grid container spacing={2}>
        {projects?.map((project) => (
          <Grid key={project.id} size={{ xs: 12, sm: 6, md: 4 }}>
            <ProjectCard project={project} />
          </Grid>
        ))}
      </Grid>
    </Stack>
  );
}

export default ProjectListPage;
