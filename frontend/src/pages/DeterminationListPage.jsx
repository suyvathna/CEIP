import { useParams, Link as RouterLink } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import Typography from "@mui/material/Typography";
import Stack from "@mui/material/Stack";
import Paper from "@mui/material/Paper";
import Button from "@mui/material/Button";
import Chip from "@mui/material/Chip";
import Alert from "@mui/material/Alert";
import CircularProgress from "@mui/material/CircularProgress";
import List from "@mui/material/List";
import ListItemButton from "@mui/material/ListItemButton";
import ListItemText from "@mui/material/ListItemText";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import ProjectNav from "../components/ProjectNav";
import EngineChip from "../components/EngineChip";
import { ENGINE_B } from "../utils/engines";
import {
  DETERMINATION_STATUS_COLORS,
  DETERMINATION_STATUS_LABELS,
} from "../utils/determination";
import { getProjectDeterminations } from "../api/determinations";

function DeterminationListPage() {
  const { projectId } = useParams();

  const query = useQuery({
    queryKey: ["determinations", projectId],
    queryFn: () => getProjectDeterminations(projectId),
  });

  const determinations = query.data || [];
  const nodOpen = determinations.filter(
    (d) => d.status === "DeterminedNodOpen"
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

      <ProjectNav projectId={projectId} active="determinations" />

      <Stack direction="row" spacing={1.5} sx={{ alignItems: "center", flexWrap: "wrap" }}>
        <Typography variant="h4" fontWeight={700}>
          Determinations
        </Typography>
        <EngineChip engine={ENGINE_B} short={false} />
      </Stack>

      <Typography variant="body2" color="text.secondary">
        Sub-Clause 3.7 governs &ldquo;any matter or Claim&rdquo;, so this
        register covers valuation disputes and measurement disagreements
        that never became a Sub-Clause 20.2 claim as well as those that
        did. Every one of them opens a 28-day Notice of Dissatisfaction
        window, and every window that closes without a Notice makes the
        Engineer&apos;s decision final and binding for good.
      </Typography>

      {nodOpen.length > 0 && (
        <Alert severity="error">
          {nodOpen.length} determination(s) with an open Notice of
          Dissatisfaction window. Check each one&apos;s remaining days
          before it closes.
        </Alert>
      )}

      {query.isLoading && <CircularProgress size={24} />}
      {query.isError && <Alert severity="error">{query.error.message}</Alert>}

      {query.data && determinations.length === 0 && (
        <Paper sx={{ p: 3 }}>
          <Typography color="text.secondary">
            Nothing here yet. A determination record opens automatically
            when a fully detailed claim is submitted — Sub-Clause 20.2.5
            sends the claim straight to 3.7, so the record has to exist
            before the Engineer&apos;s determination arrives or nothing is
            watching for the NOD window that follows it.
          </Typography>
        </Paper>
      )}

      {determinations.length > 0 && (
        <Paper>
          <List disablePadding>
            {determinations.map((determination) => (
              <ListItemButton
                key={determination.id}
                component={RouterLink}
                to={`/projects/${projectId}/determinations/${determination.id}`}
                divider
              >
                <ListItemText
                  primary={
                    <Stack
                      direction="row"
                      spacing={1}
                      sx={{ alignItems: "center", flexWrap: "wrap" }}
                    >
                      {determination.determination_no && (
                        <Chip
                          size="small"
                          variant="outlined"
                          color="primary"
                          label={determination.determination_no}
                        />
                      )}
                      <Typography variant="body1" fontWeight={600}>
                        {determination.matter_title}
                      </Typography>
                      <Chip
                        size="small"
                        color={
                          DETERMINATION_STATUS_COLORS[determination.status] ||
                          "default"
                        }
                        label={
                          DETERMINATION_STATUS_LABELS[determination.status] ||
                          determination.status
                        }
                      />
                      {determination.is_final_and_binding && (
                        <Chip size="small" color="error" label="No appeal" />
                      )}
                    </Stack>
                  }
                  secondary={`Referred ${determination.referred_date}${
                    determination.determination_received_date
                      ? ` — determination received ${determination.determination_received_date}`
                      : ""
                  }${
                    determination.nod_given_date
                      ? ` — NOD given ${determination.nod_given_date}`
                      : ""
                  }`}
                />
              </ListItemButton>
            ))}
          </List>
        </Paper>
      )}
    </Stack>
  );
}

export default DeterminationListPage;
