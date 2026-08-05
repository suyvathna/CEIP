import { useEffect, useState } from "react";
import { useParams, useNavigate, Link as RouterLink } from "react-router-dom";
import Stack from "@mui/material/Stack";
import Paper from "@mui/material/Paper";
import Typography from "@mui/material/Typography";
import Chip from "@mui/material/Chip";
import Button from "@mui/material/Button";
import CircularProgress from "@mui/material/CircularProgress";
import Alert from "@mui/material/Alert";
import Table from "@mui/material/Table";
import TableBody from "@mui/material/TableBody";
import TableCell from "@mui/material/TableCell";
import TableHead from "@mui/material/TableHead";
import TableRow from "@mui/material/TableRow";
import Grid from "@mui/material/Grid";
import AddIcon from "@mui/icons-material/Add";
import EditIcon from "@mui/icons-material/Edit";
import DeleteIcon from "@mui/icons-material/Delete";
import PictureAsPdfIcon from "@mui/icons-material/PictureAsPdf";
import TableChartIcon from "@mui/icons-material/TableChart";

import {
  getDailyLog,
  deleteDailyLog,
  dailyLogReportPdfUrl,
  dailyLogReportExcelUrl,
} from "../api/dailyLogs";
import { getDailyLogEvidence, deleteEvidence } from "../api/evidence";
import { BASE_URL } from "../api/client";

function Section({ title, children }) {
  return (
    <Paper variant="outlined" sx={{ p: 2 }}>
      <Typography variant="h6" gutterBottom>
        {title}
      </Typography>
      {children}
    </Paper>
  );
}

function EntryTable({ rows, columns, emptyLabel }) {
  if (!rows || rows.length === 0) {
    return <Typography color="text.secondary">{emptyLabel}</Typography>;
  }
  return (
    <Table size="small">
      <TableHead>
        <TableRow>
          {columns.map((c) => (
            <TableCell key={c.key}>{c.label}</TableCell>
          ))}
        </TableRow>
      </TableHead>
      <TableBody>
        {rows.map((row, i) => (
          <TableRow key={row.id || i}>
            {columns.map((c) => (
              <TableCell key={c.key}>
                {c.render ? c.render(row[c.key], row) : row[c.key] ?? ""}
              </TableCell>
            ))}
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}

function InfoField({ label, value }) {
  if (value === null || value === undefined || value === "") return null;
  return (
    <Typography variant="body2">
      <strong>{label}:</strong> {value}
    </Typography>
  );
}

function DailyLogDetailPage() {
  const { projectId, dailyLogId } = useParams();
  const navigate = useNavigate();
  const [dailyLog, setDailyLog] = useState(null);
  const [evidence, setEvidence] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [actionError, setActionError] = useState(null);

  function reload() {
    setLoading(true);
    return Promise.all([
      getDailyLog(dailyLogId),
      getDailyLogEvidence(dailyLogId),
    ])
      .then(([logData, evidenceData]) => {
        setDailyLog(logData);
        setEvidence(evidenceData || []);
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    reload();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [dailyLogId]);

  async function handleDelete() {
    const confirmed = window.confirm(
      `Delete the Daily Log for ${dailyLog.diary_date}? This cannot be undone.`
    );
    if (!confirmed) return;
    try {
      await deleteDailyLog(dailyLogId);
      navigate(`/projects/${projectId}`);
    } catch (err) {
      setActionError(err.message);
    }
  }

  async function handleDeletePhoto(item) {
    const confirmed = window.confirm("Remove this photo? This cannot be undone.");
    if (!confirmed) return;
    setActionError(null);
    try {
      await deleteEvidence(item.id);
      setEvidence((prev) => prev.filter((e) => e.id !== item.id));
    } catch (err) {
      setActionError(err.message);
    }
  }

  if (loading) return <CircularProgress />;
  if (error) return <Alert severity="error">{error}</Alert>;
  if (!dailyLog) return <Typography>Daily Log not found.</Typography>;

  return (
    <Stack spacing={2}>
      <RouterLink to={`/projects/${projectId}`}>&larr; Back to project</RouterLink>

      <Stack direction="row" sx={{ justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 1 }}>
        <Typography variant="h4">Daily Log: {dailyLog.diary_date}</Typography>
        <Stack direction="row" spacing={1} sx={{ flexWrap: "wrap" }}>
          <Button
            component="a"
            href={dailyLogReportPdfUrl(dailyLogId)}
            target="_blank"
            rel="noreferrer"
            startIcon={<PictureAsPdfIcon fontSize="small" />}
            variant="outlined"
          >
            PDF
          </Button>
          <Button
            component="a"
            href={dailyLogReportExcelUrl(dailyLogId)}
            target="_blank"
            rel="noreferrer"
            startIcon={<TableChartIcon fontSize="small" />}
            variant="outlined"
          >
            Excel
          </Button>
          <Button
            component={RouterLink}
            to={`/projects/${projectId}/daily-log/${dailyLogId}/edit`}
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
          >
            Delete
          </Button>
        </Stack>
      </Stack>

      {actionError && <Alert severity="error">{actionError}</Alert>}

      {dailyLog.linked_event_ids?.length > 0 && (
        <Stack direction="row" spacing={1} flexWrap="wrap">
          {dailyLog.linked_event_ids.map((id) => (
            <Chip
              key={id}
              component={RouterLink}
              to={`/projects/${projectId}/events/${id}`}
              clickable
              label="Linked event"
              size="small"
            />
          ))}
        </Stack>
      )}

      <Section title="Weather Report">
        <Grid container spacing={1}>
          <Grid size={{ xs: 6, sm: 3 }}><InfoField label="Temp avg" value={dailyLog.temp_avg_c != null && `${dailyLog.temp_avg_c}°C`} /></Grid>
          <Grid size={{ xs: 6, sm: 3 }}><InfoField label="Humidity avg" value={dailyLog.humidity_avg_pct != null && `${dailyLog.humidity_avg_pct}%`} /></Grid>
        </Grid>
      </Section>

      {dailyLog.daily_snapshot?.length > 0 && (
        <Section title="Daily Snapshot">
          <Stack direction="row" spacing={2} flexWrap="wrap">
            {dailyLog.daily_snapshot.map((slot, i) => (
              <Paper key={i} variant="outlined" sx={{ p: 1, minWidth: 90, textAlign: "center" }}>
                <Typography variant="caption" color="text.secondary">{slot.time}</Typography>
                <Typography variant="body2">{slot.condition || "—"}</Typography>
                <Typography variant="body2">{slot.temp_c != null ? `${slot.temp_c}°C` : ""}</Typography>
              </Paper>
            ))}
          </Stack>
        </Section>
      )}

      <Section title="Rain Records">
        <EntryTable
          rows={dailyLog.weather_observations}
          emptyLabel="No rain records logged."
          columns={[
            { key: "start_time", label: "Start" },
            { key: "end_time", label: "Finish" },
            { key: "caused_delay", label: "Delay?", render: (v) => (v ? "Yes" : "No") },
            {
              key: "evidence_id",
              label: "Photo",
              render: (evidenceId) => {
                if (!evidenceId) return "—";
                return (
                  <a href={`${BASE_URL}/evidence/download/${evidenceId}`} target="_blank" rel="noreferrer">
                    <img
                      src={`${BASE_URL}/evidence/download/${evidenceId}`}
                      alt="Rain record"
                      style={{ width: 48, height: 48, objectFit: "cover", borderRadius: 4, display: "block" }}
                    />
                  </a>
                );
              },
            },
            { key: "comments", label: "Comments" },
          ]}
        />
      </Section>

      <Section title="Notes">
        <InfoField label="Work completed / site activity" value={dailyLog.work_completed} />
        <InfoField label="Delays" value={dailyLog.delays} />
        <InfoField label="Engineer instruction" value={dailyLog.engineer_instruction} />
        <InfoField label="Plan for tomorrow" value={dailyLog.tomorrow_plan} />
        <InfoField label="Remarks" value={dailyLog.remarks} />
      </Section>

      <Section title={`Manpower Log — ${dailyLog.total_workers} workers | ${dailyLog.total_man_hours} man-hours`}>
        <EntryTable
          rows={dailyLog.manpower_entries}
          emptyLabel="No manpower rows logged."
          columns={[
            { key: "company", label: "Company" },
            { key: "trade", label: "Trade" },
            { key: "position", label: "Position" },
            { key: "workers_count", label: "Workers #" },
            { key: "hours", label: "Hours" },
            { key: "comments", label: "Comments" },
          ]}
        />
        <InfoField label="Manpower notes" value={dailyLog.manpower_notes} />
      </Section>

      <Section title="Equipment Log">
        <EntryTable
          rows={dailyLog.equipment_entries}
          emptyLabel="No equipment rows logged."
          columns={[
            { key: "equipment_name", label: "Equipment" },
            { key: "equipment_type", label: "Type" },
            { key: "hours_operating", label: "Hrs operating" },
            { key: "hours_idle", label: "Hrs idle" },
            { key: "inspected", label: "Inspected?", render: (v) => (v ? "Yes" : "No") },
            { key: "inspection_time", label: "Inspection time" },
            { key: "location", label: "Location" },
            { key: "comments", label: "Comments" },
          ]}
        />
        <InfoField label="Equipment notes" value={dailyLog.equipment_notes} />
      </Section>

      <Section title="Delivery Log">
        <EntryTable
          rows={dailyLog.delivery_entries}
          emptyLabel="No deliveries logged."
          columns={[
            { key: "delivery_time", label: "Time" },
            { key: "delivered_from", label: "Delivered from" },
            { key: "tracking_number", label: "Tracking #" },
            { key: "contents", label: "Contents" },
            { key: "comments", label: "Comments" },
          ]}
        />
        <InfoField label="Materials notes" value={dailyLog.materials_notes} />
      </Section>

      <Section title="Inspection Log">
        <EntryTable
          rows={dailyLog.inspection_entries}
          emptyLabel="No inspections logged."
          columns={[
            { key: "start_time", label: "Start" },
            { key: "end_time", label: "End" },
            { key: "inspection_type", label: "Type" },
            { key: "inspecting_entity", label: "Inspecting entity" },
            { key: "inspector_name", label: "Inspector" },
            { key: "location_area", label: "Location/area" },
            { key: "comments", label: "Comments" },
          ]}
        />
      </Section>

      <Section title="HSE">
        <EntryTable
          rows={dailyLog.hse_entries}
          emptyLabel="No HSE entries logged."
          columns={[
            { key: "entry_time", label: "Time" },
            { key: "category", label: "Category" },
            { key: "description", label: "Description" },
            { key: "action_taken", label: "Action taken" },
            { key: "reported_by", label: "Reported by" },
          ]}
        />
        <InfoField label="HSE notes" value={dailyLog.hse_notes} />
      </Section>

      <Section title="Visitors">
        <EntryTable
          rows={dailyLog.visitor_entries}
          emptyLabel="No visitors logged."
          columns={[
            { key: "time_in", label: "Time in" },
            { key: "time_out", label: "Time out" },
            { key: "visitor_name", label: "Visitor" },
            { key: "company", label: "Company" },
            { key: "purpose", label: "Purpose" },
            { key: "host_name", label: "Hosted by" },
          ]}
        />
        <InfoField label="Visitor notes" value={dailyLog.visitor_notes} />
      </Section>

      <Section title="Photos">
        <Stack direction="row" sx={{ justifyContent: "flex-end", mb: 1 }}>
          <Button
            component={RouterLink}
            to={`/projects/${projectId}/daily-log/${dailyLogId}/evidence/new`}
            startIcon={<AddIcon fontSize="small" />}
            size="small"
            variant="outlined"
          >
            Add Photo
          </Button>
        </Stack>
        {evidence.length === 0 ? (
          <Typography color="text.secondary">
            No photos yet. Photos added here (or, in future, imported
            automatically from a site camera) show up under the section
            they're tagged with.
          </Typography>
        ) : (
          <Grid container spacing={2}>
            {evidence.map((item) => (
              <Grid key={item.id} size={{ xs: 6, sm: 4, md: 3 }}>
                <Paper variant="outlined" sx={{ p: 1 }}>
                  {item.content_type?.startsWith("image/") ? (
                    <a href={`${BASE_URL}/evidence/download/${item.id}`} target="_blank" rel="noreferrer">
                      <img
                        src={`${BASE_URL}/evidence/download/${item.id}`}
                        alt={item.caption || item.filename}
                        style={{ width: "100%", height: 120, objectFit: "cover", borderRadius: 4 }}
                      />
                    </a>
                  ) : (
                    <a href={`${BASE_URL}/evidence/download/${item.id}`} target="_blank" rel="noreferrer">
                      {item.filename}
                    </a>
                  )}
                  {item.category && <Chip size="small" label={item.category} sx={{ mt: 1 }} />}
                  {item.caption && <Typography variant="caption" display="block">{item.caption}</Typography>}
                  {item.is_locked ? (
                    <Chip size="small" label="Locked" sx={{ mt: 1 }} />
                  ) : (
                    <Button size="small" color="error" onClick={() => handleDeletePhoto(item)}>
                      Remove
                    </Button>
                  )}
                </Paper>
              </Grid>
            ))}
          </Grid>
        )}
      </Section>
    </Stack>
  );
}

export default DailyLogDetailPage;
