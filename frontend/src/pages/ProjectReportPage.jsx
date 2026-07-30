import { useParams, Link as RouterLink } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import Typography from "@mui/material/Typography";
import Stack from "@mui/material/Stack";
import Paper from "@mui/material/Paper";
import Grid from "@mui/material/Grid";
import Button from "@mui/material/Button";
import CircularProgress from "@mui/material/CircularProgress";
import Alert from "@mui/material/Alert";
import Divider from "@mui/material/Divider";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import PictureAsPdfIcon from "@mui/icons-material/PictureAsPdf";
import TableChartIcon from "@mui/icons-material/TableChart";
import DataObjectIcon from "@mui/icons-material/DataObject";
import {
  getProjectReport,
  reportExportUrl,
  reportPdfUrl,
  reportExcelUrl,
} from "../api/dashboard";
import ProjectNav from "../components/ProjectNav";

function Stat({ label, value }) {
  return (
    <Grid size={{ xs: 6, sm: 4, md: 3 }}>
      <Typography variant="caption" color="text.secondary">
        {label}
      </Typography>
      <Typography variant="h5" fontWeight={700}>
        {value}
      </Typography>
    </Grid>
  );
}

function ProjectReportPage() {
  const { projectId } = useParams();

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["projectReport", projectId],
    queryFn: () => getProjectReport(projectId),
  });

  if (isLoading) return <CircularProgress />;
  if (isError) return <Alert severity="error">{error.message}</Alert>;

  return (
    <Stack spacing={2}>
      <Button
        component={RouterLink}
        to={`/projects/${projectId}`}
        size="small"
        startIcon={<ArrowBackIcon fontSize="small" />}
        sx={{ alignSelf: "flex-start" }}
      >
        Back to project
      </Button>

      <ProjectNav projectId={projectId} active="report" />

      <Stack
        direction="row"
        sx={{
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: 2,
        }}
      >
        <div>
          <Typography variant="h4" fontWeight={700}>
            {data.project_name} — Report
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Generated {new Date(data.generated_at).toLocaleString()}
          </Typography>
        </div>
        <Stack direction="row" spacing={1}>
          <Button
            component="a"
            href={reportPdfUrl(projectId)}
            target="_blank"
            rel="noreferrer"
            variant="contained"
            startIcon={<PictureAsPdfIcon fontSize="small" />}
          >
            PDF
          </Button>
          <Button
            component="a"
            href={reportExcelUrl(projectId)}
            target="_blank"
            rel="noreferrer"
            variant="outlined"
            startIcon={<TableChartIcon fontSize="small" />}
          >
            Excel
          </Button>
          <Button
            component="a"
            href={reportExportUrl(projectId)}
            target="_blank"
            rel="noreferrer"
            variant="outlined"
            startIcon={<DataObjectIcon fontSize="small" />}
          >
            JSON
          </Button>
        </Stack>
      </Stack>

      <Paper sx={{ p: 3 }}>
        <Grid container spacing={3}>
          <Stat label="Total Events" value={data.total_events} />
          <Stat label="Open Events" value={data.open_events} />
          <Stat label="Closed Events" value={data.closed_events} />
          <Stat label="Daily Diaries" value={data.total_daily_diaries} />
          <Stat label="Evidence Files" value={data.total_evidence} />
          <Stat label="High Severity" value={data.high_severity} />
          <Stat label="Medium Severity" value={data.medium_severity} />
          <Stat label="Low Severity" value={data.low_severity} />
        </Grid>

        <Divider sx={{ my: 3 }} />

        <Typography variant="subtitle2" color="text.secondary">
          Most recent event
        </Typography>
        <Typography variant="body1">
          {data.latest_event || "No events recorded yet."}
        </Typography>
      </Paper>
    </Stack>
  );
}

export default ProjectReportPage;
