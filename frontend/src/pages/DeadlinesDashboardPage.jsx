import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link as RouterLink, useParams } from "react-router-dom";
import Typography from "@mui/material/Typography";
import Stack from "@mui/material/Stack";
import Paper from "@mui/material/Paper";
import Chip from "@mui/material/Chip";
import List from "@mui/material/List";
import ListItemButton from "@mui/material/ListItemButton";
import ListItemText from "@mui/material/ListItemText";
import CircularProgress from "@mui/material/CircularProgress";
import Alert from "@mui/material/Alert";
import ToggleButton from "@mui/material/ToggleButton";
import ToggleButtonGroup from "@mui/material/ToggleButtonGroup";
import EngineExplainer from "../components/EngineExplainer";
import ProjectNav from "../components/ProjectNav";
import { ENGINE_A, ENGINE_B, ENGINE_SHORT_LABELS } from "../utils/engines";
import { getDeadlineFeed } from "../api/compliance";

/**
 * Every live deadline across both engines for THIS project, in one list,
 * soonest first.
 *
 * This screen used to assemble itself client-side: fetch every project,
 * then every claim in every project, then one more request per claim for
 * its clock. On a contractor running eight jobs with forty claims that
 * was roughly fifty sequential round trips to render one page - and it
 * could still only ever see events and claims, because compliance
 * obligations, Sub-Clause 3.7 determinations and Sub-Clause 3.5
 * instructions had nowhere to appear. It is now one request to
 * GET /compliance/deadlines?project_id=..., which computes and ranks the
 * lot server-side, scoped to this project only - deadlines are never
 * shown mixed across projects anywhere in this app.
 */

const SEVERITY_COLORS = {
  Critical: "error",
  Warning: "warning",
  Info: "info",
};

const CATEGORY_LABELS = {
  Compliance: "Compliance",
  Claim: "Claim (20.2)",
  Determination: "Determination (3.7)",
  Variation: "Variation (13 / 3.5)",
  Event: "Event notice",
};

const WINDOWS = [
  { value: 14, label: "Next 14 days" },
  { value: 30, label: "Next 30 days" },
  { value: 90, label: "Next 90 days" },
  { value: "", label: "Everything open" },
];

function DeadlinesDashboardPage() {
  const { projectId } = useParams();
  const [withinDays, setWithinDays] = useState(30);
  const [category, setCategory] = useState("");
  const [engine, setEngine] = useState("");

  const feedQuery = useQuery({
    queryKey: ["deadlineFeed", projectId, withinDays],
    queryFn: () =>
      getDeadlineFeed({
        projectId,
        withinDays: withinDays === "" ? undefined : withinDays,
      }),
  });

  if (feedQuery.isLoading) return <CircularProgress />;
  if (feedQuery.isError)
    return <Alert severity="error">{feedQuery.error.message}</Alert>;

  const feed = feedQuery.data;
  const items = feed.items
    .filter((item) => (category ? item.category === category : true))
    .filter((item) => (engine ? item.engine === engine : true));

  const categories = [...new Set(feed.items.map((item) => item.category))];

  return (
    <Stack spacing={3}>
      <ProjectNav projectId={projectId} active="deadlines" />

      <Typography variant="h4" fontWeight={700}>
        Deadlines
      </Typography>

      <Stack direction="row" spacing={1} sx={{ flexWrap: "wrap", gap: 1 }}>
        <Chip label={`${feed.total} open`} />
        <Chip color="error" label={`${feed.overdue} overdue`} />
        <Chip color="error" variant="outlined" label={`${feed.critical} critical`} />
        <Chip variant="outlined" label={`as at ${feed.generated_for}`} />
      </Stack>

      <EngineExplainer />

      {/* Engine first, category second. Which loop a deadline came from
          is the more useful cut: it separates "paperwork I owe" from
          "a clock running against my entitlement". */}
      <Stack direction="row" spacing={1} sx={{ flexWrap: "wrap", gap: 1, alignItems: "center" }}>
        <Typography variant="body2" color="text.secondary">
          Engine:
        </Typography>
        <Chip
          label={`All (${feed.total})`}
          color={engine === "" ? "primary" : "default"}
          onClick={() => setEngine("")}
        />
        <Chip
          label={`${ENGINE_SHORT_LABELS[ENGINE_A]} (${feed.engine_a ?? 0})`}
          color={engine === ENGINE_A ? "primary" : "default"}
          onClick={() => setEngine(ENGINE_A)}
        />
        <Chip
          label={`${ENGINE_SHORT_LABELS[ENGINE_B]} (${feed.engine_b ?? 0})`}
          color={engine === ENGINE_B ? "primary" : "default"}
          onClick={() => setEngine(ENGINE_B)}
        />
      </Stack>

      <ToggleButtonGroup
        exclusive
        size="small"
        value={withinDays}
        onChange={(e, value) => {
          if (value !== null) setWithinDays(value);
        }}
      >
        {WINDOWS.map((window) => (
          <ToggleButton key={String(window.value)} value={window.value}>
            {window.label}
          </ToggleButton>
        ))}
      </ToggleButtonGroup>

      <Stack direction="row" spacing={1} sx={{ flexWrap: "wrap", gap: 1 }}>
        <Chip
          label="All"
          color={category === "" ? "primary" : "default"}
          onClick={() => setCategory("")}
        />
        {categories.map((value) => (
          <Chip
            key={value}
            label={CATEGORY_LABELS[value] || value}
            color={category === value ? "primary" : "default"}
            onClick={() => setCategory(value)}
          />
        ))}
      </Stack>

      {items.length === 0 ? (
        <Paper sx={{ p: 3 }}>
          <Typography color="text.secondary">
            Nothing falls due in this window for this project. Widen it, or
            check the Compliance tab for the full register.
          </Typography>
        </Paper>
      ) : (
        <Paper>
          <List disablePadding>
            {items.map((item) => (
              <ListItemButton
                key={`${item.source_type}-${item.source_id}-${item.stage}`}
                component={RouterLink}
                to={item.link_path}
                divider
              >
                <ListItemText
                  primary={
                    <Stack
                      direction="row"
                      spacing={1}
                      sx={{ alignItems: "center", flexWrap: "wrap" }}
                    >
                      <Chip
                        size="small"
                        color={SEVERITY_COLORS[item.severity] || "default"}
                        label={
                          item.days_remaining < 0
                            ? `${Math.abs(item.days_remaining)}d overdue`
                            : `${item.days_remaining}d left`
                        }
                      />
                      {item.reference && (
                        <Chip size="small" variant="outlined" label={item.reference} />
                      )}
                      <Typography variant="body1" fontWeight={600}>
                        {item.title}
                      </Typography>
                    </Stack>
                  }
                  secondary={`${item.stage_label} — due ${
                    item.deadline
                  }${item.clause_code ? ` — ${item.clause_code}` : ""}`}
                />
              </ListItemButton>
            ))}
          </List>
        </Paper>
      )}
    </Stack>
  );
}

export default DeadlinesDashboardPage;
