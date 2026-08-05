import { useState } from "react";
import { useParams, Link as RouterLink } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import Typography from "@mui/material/Typography";
import Stack from "@mui/material/Stack";
import Paper from "@mui/material/Paper";
import Grid from "@mui/material/Grid";
import Button from "@mui/material/Button";
import ButtonBase from "@mui/material/ButtonBase";
import CircularProgress from "@mui/material/CircularProgress";
import Alert from "@mui/material/Alert";
import Divider from "@mui/material/Divider";
import TextField from "@mui/material/TextField";
import RadioGroup from "@mui/material/RadioGroup";
import Radio from "@mui/material/Radio";
import FormControlLabel from "@mui/material/FormControlLabel";
import FormLabel from "@mui/material/FormLabel";
import Checkbox from "@mui/material/Checkbox";
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
import {
  getProjectDailyLogs,
  projectDailyLogReportPdfUrl,
  projectDailyLogReportExcelUrl,
} from "../api/dailyLogs";
import ProjectNav from "../components/ProjectNav";

// Every tile links back into the project's Events/Daily Log tabs,
// pre-filtered - e.g. clicking "High Severity" jumps straight to the
// list of high-severity events instead of leaving the Contractor to
// find them by hand. "Evidence Files" has no natural destination list
// page of its own, so it stays a plain (non-clickable) number.
function Stat({ label, value, to }) {
  const content = (
    <>
      <Typography variant="caption" color="text.secondary">
        {label}
      </Typography>
      <Typography variant="h5" fontWeight={700}>
        {value}
      </Typography>
    </>
  );

  return (
    <Grid size={{ xs: 6, sm: 4, md: 3 }}>
      {to ? (
        <ButtonBase
          component={RouterLink}
          to={to}
          sx={{ display: "block", textAlign: "left", width: "100%", borderRadius: 1, p: 0.5 }}
        >
          {content}
        </ButtonBase>
      ) : (
        content
      )}
    </Grid>
  );
}

// The Report tab's Daily Log PDF picker: single day, a contiguous range,
// or several specific (possibly non-contiguous) days, each combinable
// into one PDF or exported separately (as a zip) - see
// projectDailyLogReportPdfUrl and the backend's project_daily_log_report_pdf_endpoint.
function DailyLogExportPanel({ projectId }) {
  const [mode, setMode] = useState("range");
  const [singleDate, setSingleDate] = useState("");
  const [rangeStart, setRangeStart] = useState("");
  const [rangeEnd, setRangeEnd] = useState("");
  const [selectedDates, setSelectedDates] = useState([]);
  const [separate, setSeparate] = useState(false);

  const { data: dailyLogs } = useQuery({
    queryKey: ["projectDailyLogs", projectId],
    queryFn: () => getProjectDailyLogs(projectId),
    enabled: mode === "specific",
  });

  function toggleDate(date) {
    setSelectedDates((prev) =>
      prev.includes(date) ? prev.filter((d) => d !== date) : [...prev, date]
    );
  }

  let pdfUrl = null;
  if (mode === "single") {
    if (singleDate) {
      pdfUrl = projectDailyLogReportPdfUrl(projectId, { dates: [singleDate] });
    }
  } else if (mode === "range") {
    pdfUrl = projectDailyLogReportPdfUrl(projectId, {
      startDate: rangeStart || undefined,
      endDate: rangeEnd || undefined,
      separate,
    });
  } else if (selectedDates.length > 0) {
    pdfUrl = projectDailyLogReportPdfUrl(projectId, { dates: selectedDates, separate });
  }

  // Combine/separate is meaningless for a single day. "Range" can't know
  // its day count without a fetch, so the toggle just stays visible there
  // - a range that resolves to one day behaves the same either way (see
  // the backend's len(reports) == 1 special case).
  const showSeparateToggle = mode === "range" || (mode === "specific" && selectedDates.length !== 1);

  return (
    <Stack spacing={2}>
      <FormLabel component="legend">Which day(s)?</FormLabel>
      <RadioGroup row value={mode} onChange={(e) => setMode(e.target.value)}>
        <FormControlLabel value="single" control={<Radio size="small" />} label="Single day" />
        <FormControlLabel value="range" control={<Radio size="small" />} label="Date range" />
        <FormControlLabel value="specific" control={<Radio size="small" />} label="Specific days" />
      </RadioGroup>

      {mode === "single" && (
        <TextField
          type="date"
          size="small"
          label="Date"
          value={singleDate}
          onChange={(e) => setSingleDate(e.target.value)}
          slotProps={{ inputLabel: { shrink: true } }}
          sx={{ maxWidth: 220 }}
        />
      )}

      {mode === "range" && (
        <Stack direction="row" spacing={2}>
          <TextField
            type="date"
            size="small"
            label="From"
            value={rangeStart}
            onChange={(e) => setRangeStart(e.target.value)}
            slotProps={{ inputLabel: { shrink: true } }}
          />
          <TextField
            type="date"
            size="small"
            label="To"
            value={rangeEnd}
            onChange={(e) => setRangeEnd(e.target.value)}
            slotProps={{ inputLabel: { shrink: true } }}
          />
          <Typography variant="caption" color="text.secondary" sx={{ alignSelf: "center" }}>
            Leave both blank for the whole project history.
          </Typography>
        </Stack>
      )}

      {mode === "specific" && (
        <Stack spacing={0.5} sx={{ maxHeight: 220, overflowY: "auto" }}>
          {!dailyLogs && <Typography color="text.secondary">Loading dates…</Typography>}
          {dailyLogs?.length === 0 && (
            <Typography color="text.secondary">No Daily Log entries yet.</Typography>
          )}
          {dailyLogs?.map((log) => (
            <FormControlLabel
              key={log.id}
              control={
                <Checkbox
                  size="small"
                  checked={selectedDates.includes(log.diary_date)}
                  onChange={() => toggleDate(log.diary_date)}
                />
              }
              label={log.diary_date}
            />
          ))}
        </Stack>
      )}

      {showSeparateToggle && (
        <RadioGroup
          row
          value={separate ? "separate" : "combined"}
          onChange={(e) => setSeparate(e.target.value === "separate")}
        >
          <FormControlLabel value="combined" control={<Radio size="small" />} label="Combine into one PDF" />
          <FormControlLabel value="separate" control={<Radio size="small" />} label="Export separately (zip)" />
        </RadioGroup>
      )}

      <Stack direction="row" spacing={1}>
        <Button
          component="a"
          href={pdfUrl || undefined}
          target="_blank"
          rel="noreferrer"
          variant="contained"
          startIcon={<PictureAsPdfIcon fontSize="small" />}
          disabled={!pdfUrl}
        >
          PDF
        </Button>
        <Button
          component="a"
          href={
            mode === "range"
              ? projectDailyLogReportExcelUrl(projectId, { startDate: rangeStart, endDate: rangeEnd })
              : projectDailyLogReportExcelUrl(projectId)
          }
          target="_blank"
          rel="noreferrer"
          variant="outlined"
          startIcon={<TableChartIcon fontSize="small" />}
        >
          Excel
        </Button>
        <Typography variant="caption" color="text.secondary" sx={{ alignSelf: "center" }}>
          {mode === "range"
            ? "Uses the date range above."
            : "Excel export doesn't support day-picking yet - whole project history."}
        </Typography>
      </Stack>
    </Stack>
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

  const eventsBase = `/projects/${projectId}?tab=events`;
  const dailyLogLink = `/projects/${projectId}?tab=dailyLog`;

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
          <Stat label="Total Events" value={data.total_events} to={eventsBase} />
          <Stat label="Open Events" value={data.open_events} to={`${eventsBase}&status=Open`} />
          <Stat label="Closed Events" value={data.closed_events} to={`${eventsBase}&status=Closed`} />
          <Stat label="Daily Logs" value={data.total_daily_logs} to={dailyLogLink} />
          <Stat label="Evidence Files" value={data.total_evidence} />
          <Stat label="High Severity" value={data.high_severity} to={`${eventsBase}&severity=High`} />
          <Stat label="Medium Severity" value={data.medium_severity} to={`${eventsBase}&severity=Medium`} />
          <Stat label="Low Severity" value={data.low_severity} to={`${eventsBase}&severity=Low`} />
        </Grid>

        <Divider sx={{ my: 3 }} />

        <Typography variant="subtitle2" color="text.secondary">
          Most recent event
        </Typography>
        <Typography variant="body1">
          {data.latest_event || "No events recorded yet."}
        </Typography>
      </Paper>

      <Paper sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom>
          Daily Log Export
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Pick the day(s) you need, formatted to match your site's daily
          log template - ready to hand an Engineer or DAAB alongside a
          claim. Files are named "{"{project code}"}-DL-{"{date}"}.pdf".
        </Typography>
        <DailyLogExportPanel projectId={projectId} />
      </Paper>
    </Stack>
  );
}

export default ProjectReportPage;
