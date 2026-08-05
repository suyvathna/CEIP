import { useMemo } from "react";
import { Link as RouterLink, useParams, useSearchParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import Typography from "@mui/material/Typography";
import Stack from "@mui/material/Stack";
import Paper from "@mui/material/Paper";
import List from "@mui/material/List";
import ListItemButton from "@mui/material/ListItemButton";
import ListItemText from "@mui/material/ListItemText";
import Divider from "@mui/material/Divider";
import Chip from "@mui/material/Chip";
import CircularProgress from "@mui/material/CircularProgress";
import Alert from "@mui/material/Alert";
import EventNoteIcon from "@mui/icons-material/EventNote";
import DescriptionIcon from "@mui/icons-material/Description";
import AttachFileIcon from "@mui/icons-material/AttachFile";
import ProjectNav from "../components/ProjectNav";
import { searchIntelligence } from "../api/intelligence";
import { BASE_URL } from "../api/client";

const ICONS = {
  Event: <EventNoteIcon fontSize="small" />,
  "Daily Log": <DescriptionIcon fontSize="small" />,
  Evidence: <AttachFileIcon fontSize="small" />,
};

// Results are already scoped to this project (see searchIntelligence), so
// every link resolves straight to its project-scoped route - no redirect
// hop needed to look up which project an id belongs to.
function resultLink(result, projectId) {
  if (result.item_type === "Event") return `/projects/${projectId}/events/${result.id}`;
  if (result.item_type === "Daily Log") return `/projects/${projectId}/daily-log/${result.id}`;
  return null;
}

function SearchResultsPage() {
  const { projectId } = useParams();
  const [searchParams] = useSearchParams();
  const q = searchParams.get("q") || "";

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["intelligenceSearch", projectId, q],
    queryFn: () => searchIntelligence(q, projectId),
    enabled: q.length > 0,
  });

  const grouped = useMemo(() => {
    const map = new Map();
    for (const result of data || []) {
      if (!map.has(result.item_type)) map.set(result.item_type, []);
      map.get(result.item_type).push(result);
    }
    return [...map.entries()];
  }, [data]);

  return (
    <Stack spacing={2}>
      <ProjectNav projectId={projectId} active={false} />

      <Typography variant="h4" fontWeight={700}>
        Search results
      </Typography>
      <Typography variant="body2" color="text.secondary">
        {q ? `Showing results for "${q}"` : "Enter a search term in the top bar."}
      </Typography>

      {isLoading && <CircularProgress />}
      {isError && <Alert severity="error">{error.message}</Alert>}

      {data && data.length === 0 && (
        <Typography color="text.secondary">
          No events, Daily Logs, or evidence matched that search.
        </Typography>
      )}

      {grouped.map(([itemType, results]) => (
        <Paper key={itemType}>
          <Typography
            variant="subtitle1"
            fontWeight={600}
            sx={{ p: 2, pb: 1 }}
          >
            {itemType} ({results.length})
          </Typography>
          <List disablePadding>
            {results.map((result, idx) => {
              const href = resultLink(result, projectId);
              const isEvidence = result.item_type === "Evidence";

              return (
                <div key={result.id}>
                  {idx > 0 && <Divider component="li" />}
                  <ListItemButton
                    component={isEvidence ? "a" : RouterLink}
                    to={!isEvidence ? href : undefined}
                    href={isEvidence ? `${BASE_URL}/evidence/download/${result.id}` : undefined}
                    target={isEvidence ? "_blank" : undefined}
                    rel={isEvidence ? "noreferrer" : undefined}
                  >
                    <Stack direction="row" spacing={1} sx={{ alignItems: "center", mr: 1 }}>
                      {ICONS[itemType]}
                    </Stack>
                    <ListItemText
                      primary={result.title || "(untitled)"}
                      secondary={new Date(result.created_at).toLocaleString()}
                    />
                    {isEvidence && (
                      <Chip label="Download" size="small" variant="outlined" />
                    )}
                  </ListItemButton>
                </div>
              );
            })}
          </List>
        </Paper>
      ))}
    </Stack>
  );
}

export default SearchResultsPage;
