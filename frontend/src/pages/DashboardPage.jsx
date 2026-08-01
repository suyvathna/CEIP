import { useParams, Link as RouterLink } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  PieChart,
  Pie,
  Cell,
  Legend,
} from "recharts";
import Typography from "@mui/material/Typography";
import Stack from "@mui/material/Stack";
import Paper from "@mui/material/Paper";
import Grid from "@mui/material/Grid";
import CircularProgress from "@mui/material/CircularProgress";
import Alert from "@mui/material/Alert";
import Chip from "@mui/material/Chip";
import List from "@mui/material/List";
import ListItemButton from "@mui/material/ListItemButton";
import ListItemText from "@mui/material/ListItemText";
import Divider from "@mui/material/Divider";
import Button from "@mui/material/Button";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import { getDashboard } from "../api/dashboard";
import ProjectNav from "../components/ProjectNav";
import { severityColor, statusColor } from "../theme";

const SEVERITY_COLORS = {
  High: "#a3231c",
  Medium: "#8a6100",
  Low: "#1f6b3a",
};

function StatCard({ label, value }) {
  return (
    <Paper sx={{ p: 2, height: "100%" }}>
      <Typography variant="caption" color="text.secondary">
        {label}
      </Typography>
      <Typography variant="h4" fontWeight={700}>
        {value}
      </Typography>
    </Paper>
  );
}

function DashboardPage() {
  const { projectId } = useParams();

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["dashboard", projectId],
    queryFn: () => getDashboard(projectId),
  });

  if (isLoading) return <CircularProgress />;
  if (isError) return <Alert severity="error">{error.message}</Alert>;

  const severityData = [
    { name: "High", value: data.high_severity_events },
    { name: "Medium", value: data.medium_severity_events },
    { name: "Low", value: data.low_severity_events },
  ].filter((d) => d.value > 0);

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

      <ProjectNav projectId={projectId} active="dashboard" />

      <Typography variant="h4" fontWeight={700}>
        {data.project_name} — Dashboard
      </Typography>

      <Grid container spacing={2}>
        <Grid size={{ xs: 6, sm: 4, md: 2.4 }}>
          <StatCard label="Total Events" value={data.total_events} />
        </Grid>
        <Grid size={{ xs: 6, sm: 4, md: 2.4 }}>
          <StatCard label="Open Events" value={data.open_events} />
        </Grid>
        <Grid size={{ xs: 6, sm: 4, md: 2.4 }}>
          <StatCard label="Closed Events" value={data.closed_events} />
        </Grid>
        <Grid size={{ xs: 6, sm: 4, md: 2.4 }}>
          <StatCard label="Daily Logs" value={data.total_daily_logs} />
        </Grid>
        <Grid size={{ xs: 6, sm: 4, md: 2.4 }}>
          <StatCard label="Evidence Files" value={data.total_evidence} />
        </Grid>
      </Grid>

      <Grid container spacing={2}>
        <Grid size={{ xs: 12, md: 7 }}>
          <Paper sx={{ p: 2, height: 340 }}>
            <Typography variant="subtitle1" fontWeight={600} gutterBottom>
              Events by Type
            </Typography>
            {data.event_type_statistics.length === 0 ? (
              <Typography color="text.secondary">No events yet.</Typography>
            ) : (
              <ResponsiveContainer width="100%" height="88%">
                <BarChart data={data.event_type_statistics}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="event_type" tick={{ fontSize: 12 }} />
                  <YAxis allowDecimals={false} />
                  <Tooltip />
                  <Bar dataKey="total" fill="#2f6f4f" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </Paper>
        </Grid>
        <Grid size={{ xs: 12, md: 5 }}>
          <Paper sx={{ p: 2, height: 340 }}>
            <Typography variant="subtitle1" fontWeight={600} gutterBottom>
              Severity Breakdown
            </Typography>
            {severityData.length === 0 ? (
              <Typography color="text.secondary">No events yet.</Typography>
            ) : (
              <ResponsiveContainer width="100%" height="88%">
                <PieChart>
                  <Pie
                    data={severityData}
                    dataKey="value"
                    nameKey="name"
                    innerRadius={50}
                    outerRadius={90}
                    paddingAngle={2}
                  >
                    {severityData.map((entry) => (
                      <Cell key={entry.name} fill={SEVERITY_COLORS[entry.name]} />
                    ))}
                  </Pie>
                  <Legend />
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            )}
          </Paper>
        </Grid>
      </Grid>

      <Paper>
        <Typography variant="subtitle1" fontWeight={600} sx={{ p: 2, pb: 0 }}>
          Recent Events
        </Typography>
        {data.recent_events.length === 0 ? (
          <Typography color="text.secondary" sx={{ p: 2 }}>
            No events yet.
          </Typography>
        ) : (
          <List disablePadding>
            {data.recent_events.map((event, idx) => (
              <div key={event.id}>
                {idx > 0 && <Divider component="li" />}
                <ListItemButton
                  component={RouterLink}
                  to={`/projects/${projectId}/events/${event.id}`}
                >
                  <ListItemText
                    primary={event.title}
                    secondary={event.event_type}
                  />
                  <Stack direction="row" spacing={1}>
                    <Chip
                      label={event.severity}
                      color={severityColor(event.severity)}
                      size="small"
                      variant="outlined"
                    />
                    <Chip
                      label={event.status}
                      color={statusColor(event.status)}
                      size="small"
                    />
                  </Stack>
                </ListItemButton>
              </div>
            ))}
          </List>
        )}
      </Paper>
    </Stack>
  );
}

export default DashboardPage;
