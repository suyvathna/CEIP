import { useState } from "react";
import { useParams, Link as RouterLink } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useSnackbar } from "notistack";
import Typography from "@mui/material/Typography";
import Stack from "@mui/material/Stack";
import Paper from "@mui/material/Paper";
import Button from "@mui/material/Button";
import TextField from "@mui/material/TextField";
import MenuItem from "@mui/material/MenuItem";
import Table from "@mui/material/Table";
import TableHead from "@mui/material/TableHead";
import TableBody from "@mui/material/TableBody";
import TableRow from "@mui/material/TableRow";
import TableCell from "@mui/material/TableCell";
import Chip from "@mui/material/Chip";
import CircularProgress from "@mui/material/CircularProgress";
import Alert from "@mui/material/Alert";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import { getProjectEvents } from "../api/events";
import {
  getProjectActivities,
  createActivity,
  addPredecessor,
  getProjectCPM,
  createEventImpact,
} from "../api/programme";
import ProjectNav from "../components/ProjectNav";

function ProgrammePage() {
  const { projectId } = useParams();
  const { enqueueSnackbar } = useSnackbar();
  const queryClient = useQueryClient();

  const activitiesQuery = useQuery({
    queryKey: ["activities", projectId],
    queryFn: () => getProjectActivities(projectId),
  });

  const cpmQuery = useQuery({
    queryKey: ["cpm", projectId],
    queryFn: () => getProjectCPM(projectId),
    retry: false,
  });

  const eventsQuery = useQuery({
    queryKey: ["projectEvents", projectId],
    queryFn: () => getProjectEvents(projectId),
  });

  const [form, setForm] = useState({
    activity_code: "",
    name: "",
    planned_start: "",
    planned_finish: "",
  });
  const [predecessorForm, setPredecessorForm] = useState({ activity: "", predecessor: "" });
  const [impactForm, setImpactForm] = useState({
    event_id: "",
    activity_id: "",
    impact_days: "",
    risk_category: "EmployerRisk",
    notes: "",
  });

  function refresh() {
    queryClient.invalidateQueries({ queryKey: ["activities", projectId] });
    queryClient.invalidateQueries({ queryKey: ["cpm", projectId] });
  }

  const createActivityMutation = useMutation({
    mutationFn: () => createActivity(projectId, form),
    onSuccess: () => {
      setForm({ activity_code: "", name: "", planned_start: "", planned_finish: "" });
      refresh();
    },
    onError: (err) => enqueueSnackbar(err.message, { variant: "error" }),
  });

  const predecessorMutation = useMutation({
    mutationFn: () =>
      addPredecessor(predecessorForm.activity, predecessorForm.predecessor),
    onSuccess: () => {
      setPredecessorForm({ activity: "", predecessor: "" });
      refresh();
    },
    onError: (err) => enqueueSnackbar(err.message, { variant: "error" }),
  });

  const impactMutation = useMutation({
    mutationFn: () =>
      createEventImpact(impactForm.event_id, {
        activity_id: impactForm.activity_id,
        impact_days: Number(impactForm.impact_days),
        risk_category: impactForm.risk_category,
        notes: impactForm.notes || null,
      }),
    onSuccess: () => {
      setImpactForm({
        event_id: "",
        activity_id: "",
        impact_days: "",
        risk_category: "EmployerRisk",
        notes: "",
      });
      refresh();
      enqueueSnackbar("Impact recorded", { variant: "success" });
    },
    onError: (err) => enqueueSnackbar(err.message, { variant: "error" }),
  });

  const activities = activitiesQuery.data || [];
  const cpmByActivityId = Object.fromEntries(
    (cpmQuery.data?.activities || []).map((a) => [a.id, a])
  );

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

      <ProjectNav projectId={projectId} active="programme" />

      <Typography variant="h4" fontWeight={700}>
        Programme
      </Typography>
      <Typography variant="body2" color="text.secondary">
        A simplified critical-path programme: finish-to-start logic only,
        no lags or resource loading. Enough to run a real critical-path
        delay calculation over hand-entered or spreadsheet-derived
        activities - see the strategy notes for the phased CPM/TIA scope.
      </Typography>

      <Paper sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom>
          Activities
        </Typography>

        {activitiesQuery.isLoading && <CircularProgress size={20} />}

        {activities.length > 0 && (
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Code</TableCell>
                <TableCell>Name</TableCell>
                <TableCell>Planned start</TableCell>
                <TableCell>Planned finish</TableCell>
                <TableCell>Early start / finish</TableCell>
                <TableCell>Total float</TableCell>
                <TableCell>Critical?</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {activities.map((a) => {
                const cpm = cpmByActivityId[a.id];
                return (
                  <TableRow key={a.id}>
                    <TableCell>{a.activity_code}</TableCell>
                    <TableCell>{a.name}</TableCell>
                    <TableCell>{a.planned_start}</TableCell>
                    <TableCell>{a.planned_finish}</TableCell>
                    <TableCell>
                      {cpm ? `${cpm.early_start} → ${cpm.early_finish}` : "—"}
                    </TableCell>
                    <TableCell>{cpm ? cpm.total_float : "—"}</TableCell>
                    <TableCell>
                      {cpm ? (
                        <Chip
                          size="small"
                          label={cpm.is_critical ? "Critical" : "Has float"}
                          color={cpm.is_critical ? "error" : "success"}
                        />
                      ) : (
                        "—"
                      )}
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        )}

        {activities.length > 0 && cpmQuery.isError && (
          <Alert severity="warning" sx={{ mt: 2 }}>
            Could not compute the critical path for the current activities
            and predecessor links - check for a logic cycle (an activity
            can't be its own predecessor, even indirectly).
          </Alert>
        )}

        {cpmQuery.data && (
          <Typography variant="body2" sx={{ mt: 2 }} color="text.secondary">
            Baseline project finish (critical path): <strong>{cpmQuery.data.project_finish}</strong>
          </Typography>
        )}

        <Stack direction="row" spacing={1} sx={{ mt: 3, flexWrap: "wrap" }}>
          <TextField
            size="small"
            label="Activity code"
            value={form.activity_code}
            onChange={(e) => setForm({ ...form, activity_code: e.target.value })}
          />
          <TextField
            size="small"
            label="Name"
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
          />
          <TextField
            size="small"
            type="date"
            label="Planned start"
            slotProps={{ inputLabel: { shrink: true } }}
            value={form.planned_start}
            onChange={(e) => setForm({ ...form, planned_start: e.target.value })}
          />
          <TextField
            size="small"
            type="date"
            label="Planned finish"
            slotProps={{ inputLabel: { shrink: true } }}
            value={form.planned_finish}
            onChange={(e) => setForm({ ...form, planned_finish: e.target.value })}
          />
          <Button
            variant="outlined"
            disabled={
              !form.activity_code ||
              !form.name ||
              !form.planned_start ||
              !form.planned_finish ||
              createActivityMutation.isPending
            }
            onClick={() => createActivityMutation.mutate()}
          >
            Add activity
          </Button>
        </Stack>
      </Paper>

      <Paper sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom>
          Predecessor links (finish-to-start)
        </Typography>
        <Stack direction="row" spacing={1} sx={{ flexWrap: "wrap" }}>
          <TextField
            select
            size="small"
            label="Activity"
            sx={{ minWidth: 220 }}
            value={predecessorForm.activity}
            onChange={(e) =>
              setPredecessorForm({ ...predecessorForm, activity: e.target.value })
            }
          >
            {activities.map((a) => (
              <MenuItem key={a.id} value={a.id}>
                {a.activity_code} — {a.name}
              </MenuItem>
            ))}
          </TextField>
          <TextField
            select
            size="small"
            label="Cannot start until this finishes"
            sx={{ minWidth: 220 }}
            value={predecessorForm.predecessor}
            onChange={(e) =>
              setPredecessorForm({ ...predecessorForm, predecessor: e.target.value })
            }
          >
            {activities.map((a) => (
              <MenuItem key={a.id} value={a.id}>
                {a.activity_code} — {a.name}
              </MenuItem>
            ))}
          </TextField>
          <Button
            variant="outlined"
            disabled={
              !predecessorForm.activity ||
              !predecessorForm.predecessor ||
              predecessorForm.activity === predecessorForm.predecessor ||
              predecessorMutation.isPending
            }
            onClick={() => predecessorMutation.mutate()}
          >
            Link
          </Button>
        </Stack>
      </Paper>

      <Paper sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom>
          Record an event's impact on an activity
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          This is the causal link a claim's delay analysis runs on - how
          many days a specific logged event pushed a specific activity,
          and whose risk it falls under.
        </Typography>
        <Stack direction="row" spacing={1} sx={{ flexWrap: "wrap" }}>
          <TextField
            select
            size="small"
            label="Event"
            sx={{ minWidth: 220 }}
            value={impactForm.event_id}
            onChange={(e) => setImpactForm({ ...impactForm, event_id: e.target.value })}
          >
            {(eventsQuery.data || []).map((event) => (
              <MenuItem key={event.id} value={event.id}>
                {event.event_date} — {event.title}
              </MenuItem>
            ))}
          </TextField>
          <TextField
            select
            size="small"
            label="Activity"
            sx={{ minWidth: 220 }}
            value={impactForm.activity_id}
            onChange={(e) => setImpactForm({ ...impactForm, activity_id: e.target.value })}
          >
            {activities.map((a) => (
              <MenuItem key={a.id} value={a.id}>
                {a.activity_code} — {a.name}
              </MenuItem>
            ))}
          </TextField>
          <TextField
            size="small"
            type="number"
            label="Impact days"
            sx={{ width: 120 }}
            value={impactForm.impact_days}
            onChange={(e) => setImpactForm({ ...impactForm, impact_days: e.target.value })}
          />
          <TextField
            select
            size="small"
            label="Risk"
            sx={{ minWidth: 160 }}
            value={impactForm.risk_category}
            onChange={(e) =>
              setImpactForm({ ...impactForm, risk_category: e.target.value })
            }
          >
            {["EmployerRisk", "ContractorRisk", "Neutral"].map((r) => (
              <MenuItem key={r} value={r}>
                {r}
              </MenuItem>
            ))}
          </TextField>
          <Button
            variant="contained"
            disabled={
              !impactForm.event_id ||
              !impactForm.activity_id ||
              !impactForm.impact_days ||
              impactMutation.isPending
            }
            onClick={() => impactMutation.mutate()}
          >
            Record impact
          </Button>
        </Stack>
      </Paper>
    </Stack>
  );
}

export default ProgrammePage;
