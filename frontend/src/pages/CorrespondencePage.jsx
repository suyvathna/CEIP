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
import AddIcon from "@mui/icons-material/Add";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import { getProjectCorrespondence } from "../api/correspondence";
import ProjectNav from "../components/ProjectNav";
import { directionColor } from "../theme";

function CorrespondencePage() {
  const { projectId } = useParams();

  const query = useQuery({
    queryKey: ["correspondence", projectId],
    queryFn: () => getProjectCorrespondence(projectId),
  });

  const items = query.data || [];

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

      <ProjectNav projectId={projectId} active="correspondence" />

      <Stack
        direction="row"
        sx={{ justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 1 }}
      >
        <Typography variant="h4" fontWeight={700}>
          Correspondence
        </Typography>
        <Button
          component={RouterLink}
          to={`/projects/${projectId}/correspondence/new`}
          startIcon={<AddIcon fontSize="small" />}
          variant="contained"
        >
          Log correspondence
        </Button>
      </Stack>

      <Typography variant="body2" color="text.secondary">
        What the Contractor sent to the Engineer, and what came back —
        this platform is Contractor-only, so every exchange with the
        Engineer happens outside it (email, post, hand delivery) and this
        register is just the record that it happened.
      </Typography>

      {query.isLoading && <CircularProgress size={24} />}
      {query.isError && <Alert severity="error">{query.error.message}</Alert>}

      {query.data && items.length === 0 && (
        <Paper sx={{ p: 3 }}>
          <Typography color="text.secondary">
            Nothing logged yet. Log every letter, email or transmittal
            sent to or received from the Engineer — a correspondence
            register is exactly the kind of contemporaneous record that
            matters when a notice's timing is later disputed.
          </Typography>
        </Paper>
      )}

      {items.length > 0 && (
        <Paper>
          <List disablePadding>
            {items.map((item) => (
              <ListItemButton
                key={item.id}
                component={RouterLink}
                to={`/projects/${projectId}/correspondence/${item.id}`}
                divider
              >
                <ListItemText
                  primary={
                    <Stack direction="row" spacing={1} sx={{ alignItems: "center", flexWrap: "wrap" }}>
                      {item.correspondence_no && (
                        <Chip size="small" variant="outlined" color="primary" label={item.correspondence_no} />
                      )}
                      <Chip
                        size="small"
                        color={directionColor(item.direction)}
                        label={item.direction}
                      />
                      <Typography variant="body1" fontWeight={600}>
                        {item.subject}
                      </Typography>
                      {item.method && (
                        <Chip size="small" variant="outlined" label={item.method} />
                      )}
                    </Stack>
                  }
                  secondary={`${item.correspondence_date}${
                    item.reference ? ` — ref ${item.reference}` : ""
                  }${item.related_to ? ` — re: ${item.related_to}` : ""}`}
                />
              </ListItemButton>
            ))}
          </List>
        </Paper>
      )}
    </Stack>
  );
}

export default CorrespondencePage;
