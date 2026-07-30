import { useMemo, useState } from "react";
import { useParams, Link as RouterLink } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from "recharts";
import Typography from "@mui/material/Typography";
import Stack from "@mui/material/Stack";
import Paper from "@mui/material/Paper";
import Grid from "@mui/material/Grid";
import TextField from "@mui/material/TextField";
import MenuItem from "@mui/material/MenuItem";
import Button from "@mui/material/Button";
import Chip from "@mui/material/Chip";
import CircularProgress from "@mui/material/CircularProgress";
import Alert from "@mui/material/Alert";
import Card from "@mui/material/Card";
import CardActionArea from "@mui/material/CardActionArea";
import CardContent from "@mui/material/CardContent";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import ClearIcon from "@mui/icons-material/Clear";
import { getProjectTimeline, getTimelineAnalytics } from "../api/timeline";
import ProjectNav from "../components/ProjectNav";
import { severityColor, statusColor } from "../theme";

const EVENT_TYPES = [
  "Progress", "Delay", "Weather", "Quality", "Safety",
  "RFI", "Instruction", "Inspection", "Delivery", "Incident", "Other",
];
const SEVERITIES = ["Low", "Medium", "High"];

function groupByDate(events) {
  const groups = new Map();
  for (const event of events) {
    if (!groups.has(event.event_date)) groups.set(event.event_date, []);
    groups.get(event.event_date).push(event);
  }
  return [...groups.entries()];
}

function TimelinePage() {
  const { projectId } = useParams();
  const [filters, setFilters] = useState({});

  const { register, handleSubmit, reset } = useForm({
    defaultValues: {
      startDate: "",
      endDate: "",
      eventType: "",
      severity: "",
    },
  });

  const timelineQuery = useQuery({
    queryKey: ["timeline", projectId, filters],
    queryFn: () => getProjectTimeline(projectId, filters),
  });

  const analyticsQuery = useQuery({
    queryKey: ["timelineAnalytics", projectId],
    queryFn: () => getTimelineAnalytics(projectId),
  });

  const analyticsChartData = useMemo(
    () =>
      (analyticsQuery.data || []).map((day) => ({
        date: day.event_date,
        total: day.total_events,
      })),
    [analyticsQuery.data]
  );

  const grouped = useMemo(
    () => groupByDate(timelineQuery.data?.events || []),
    [timelineQuery.data]
  );

  function onApplyFilters(values) {
    setFilters({
      startDate: values.startDate || undefined,
      endDate: values.endDate || undefined,
      eventType: values.eventType || undefined,
      severity: values.severity || undefined,
    });
  }

  function handleClear() {
    reset();
    setFilters({});
  }

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

      <ProjectNav projectId={projectId} active="timeline" />

      <Typography variant="h4" fontWeight={700}>
        Timeline
      </Typography>

      {analyticsChartData.length > 0 && (
        <Paper sx={{ p: 2, height: 180 }}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={analyticsChartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" tick={{ fontSize: 11 }} />
              <YAxis allowDecimals={false} width={30} />
              <Tooltip />
              <Bar dataKey="total" fill="#2f6f4f" radius={[3, 3, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </Paper>
      )}

      <Paper sx={{ p: 2 }}>
        <Stack
          component="form"
          onSubmit={handleSubmit(onApplyFilters)}
          direction="row"
          spacing={2}
          useFlexGap
          sx={{ flexWrap: "wrap", alignItems: "center" }}
        >
          <TextField
            {...register("startDate")}
            label="Start date"
            type="date"
            size="small"
            slotProps={{ inputLabel: { shrink: true } }}
          />
          <TextField
            {...register("endDate")}
            label="End date"
            type="date"
            size="small"
            slotProps={{ inputLabel: { shrink: true } }}
          />
          <TextField
            {...register("eventType")}
            label="Event type"
            select
            size="small"
            sx={{ minWidth: 160 }}
            defaultValue=""
          >
            <MenuItem value="">Any</MenuItem>
            {EVENT_TYPES.map((type) => (
              <MenuItem key={type} value={type}>
                {type}
              </MenuItem>
            ))}
          </TextField>
          <TextField
            {...register("severity")}
            label="Severity"
            select
            size="small"
            sx={{ minWidth: 140 }}
            defaultValue=""
          >
            <MenuItem value="">Any</MenuItem>
            {SEVERITIES.map((sev) => (
              <MenuItem key={sev} value={sev}>
                {sev}
              </MenuItem>
            ))}
          </TextField>
          <Button type="submit" variant="contained">
            Apply
          </Button>
          <Button
            type="button"
            onClick={handleClear}
            startIcon={<ClearIcon fontSize="small" />}
          >
            Clear
          </Button>
        </Stack>
      </Paper>

      {timelineQuery.isLoading && <CircularProgress />}
      {timelineQuery.isError && (
        <Alert severity="error">{timelineQuery.error.message}</Alert>
      )}

      {timelineQuery.data && (
        <Typography variant="body2" color="text.secondary">
          {timelineQuery.data.total_events} event
          {timelineQuery.data.total_events === 1 ? "" : "s"} matched
        </Typography>
      )}

      {grouped.length === 0 && timelineQuery.data && (
        <Typography color="text.secondary">
          No events match these filters.
        </Typography>
      )}

      <Stack spacing={2}>
        {grouped.map(([date, events]) => (
          <Grid container spacing={2} key={date}>
            <Grid size={{ xs: 12, sm: 2 }}>
              <Typography variant="subtitle2" fontWeight={700} sx={{ pt: 1 }}>
                {date}
              </Typography>
            </Grid>
            <Grid size={{ xs: 12, sm: 10 }}>
              <Stack spacing={1}>
                {events.map((event) => (
                  <Card key={event.id} variant="outlined">
                    <CardActionArea
                      component={RouterLink}
                      to={`/projects/${projectId}/events/${event.id}`}
                    >
                      <CardContent>
                        <Stack
                          direction="row"
                          sx={{
                            justifyContent: "space-between",
                            alignItems: "flex-start",
                            flexWrap: "wrap",
                            gap: 1,
                          }}
                        >
                          <div>
                            <Typography variant="subtitle2" fontWeight={600}>
                              {event.event_time} — {event.title}
                            </Typography>
                            {event.location && (
                              <Typography variant="body2" color="text.secondary">
                                {event.location}
                              </Typography>
                            )}
                          </div>
                          <Stack direction="row" spacing={1}>
                            <Chip label={event.event_type} size="small" />
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
                        </Stack>
                      </CardContent>
                    </CardActionArea>
                  </Card>
                ))}
              </Stack>
            </Grid>
          </Grid>
        ))}
      </Stack>
    </Stack>
  );
}

export default TimelinePage;
