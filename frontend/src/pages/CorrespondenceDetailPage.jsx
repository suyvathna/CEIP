import { useParams, Link as RouterLink } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Typography from "@mui/material/Typography";
import Stack from "@mui/material/Stack";
import Paper from "@mui/material/Paper";
import Button from "@mui/material/Button";
import Chip from "@mui/material/Chip";
import Alert from "@mui/material/Alert";
import CircularProgress from "@mui/material/CircularProgress";
import List from "@mui/material/List";
import ListItem from "@mui/material/ListItem";
import ListItemText from "@mui/material/ListItemText";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import AddIcon from "@mui/icons-material/Add";
import ProjectNav from "../components/ProjectNav";
import { getCorrespondence } from "../api/correspondence";
import { getCorrespondenceEvidence, deleteEvidence } from "../api/evidence";
import { BASE_URL } from "../api/client";
import { directionColor } from "../theme";

function CorrespondenceDetailPage() {
  const { projectId, correspondenceId } = useParams();
  const queryClient = useQueryClient();

  const detailQuery = useQuery({
    queryKey: ["correspondence-detail", correspondenceId],
    queryFn: () => getCorrespondence(correspondenceId),
  });

  const evidenceQuery = useQuery({
    queryKey: ["correspondenceEvidence", correspondenceId],
    queryFn: () => getCorrespondenceEvidence(correspondenceId),
  });

  const deleteMutation = useMutation({
    mutationFn: (evidenceId) => deleteEvidence(evidenceId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["correspondenceEvidence", correspondenceId] });
    },
  });

  if (detailQuery.isLoading) return <CircularProgress />;
  if (detailQuery.isError)
    return <Alert severity="error">{detailQuery.error.message}</Alert>;

  const item = detailQuery.data;
  const attachments = evidenceQuery.data || [];

  return (
    <Stack spacing={2}>
      <Button
        component={RouterLink}
        to={`/projects/${projectId}/correspondence`}
        size="small"
        startIcon={<ArrowBackIcon fontSize="small" />}
        sx={{ alignSelf: "flex-start" }}
      >
        Back to correspondence
      </Button>

      <ProjectNav projectId={projectId} active="correspondence" />

      <Stack direction="row" spacing={1} sx={{ alignItems: "center", flexWrap: "wrap" }}>
        {item.correspondence_no && (
          <Chip variant="outlined" color="primary" label={item.correspondence_no} />
        )}
        <Chip color={directionColor(item.direction)} label={item.direction} />
        <Typography variant="h4" fontWeight={700}>
          {item.subject}
        </Typography>
      </Stack>

      <Typography variant="body2" color="text.secondary">
        {item.correspondence_date}
        {item.reference ? ` — ref ${item.reference}` : ""}
        {item.method ? ` — ${item.method}` : ""}
        {item.related_to ? ` — re: ${item.related_to}` : ""}
      </Typography>

      {item.summary && (
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            Summary
          </Typography>
          <Typography variant="body2" sx={{ whiteSpace: "pre-wrap" }}>
            {item.summary}
          </Typography>
        </Paper>
      )}

      <Paper sx={{ p: 3 }}>
        <Stack direction="row" sx={{ justifyContent: "space-between", alignItems: "center" }}>
          <Typography variant="h6">Attachments</Typography>
          <Button
            size="small"
            component={RouterLink}
            to={`/projects/${projectId}/correspondence/${correspondenceId}/evidence/new`}
            startIcon={<AddIcon fontSize="small" />}
          >
            Add attachment
          </Button>
        </Stack>

        {evidenceQuery.isLoading && <CircularProgress size={20} />}

        {evidenceQuery.data && attachments.length === 0 && (
          <Typography color="text.secondary">No attachments yet.</Typography>
        )}

        {attachments.length > 0 && (
          <List disablePadding>
            {attachments.map((attachment) => (
              <ListItem
                key={attachment.id}
                divider
                secondaryAction={
                  attachment.is_locked ? (
                    <Chip size="small" label="Locked" />
                  ) : (
                    <Button
                      size="small"
                      color="error"
                      onClick={() => deleteMutation.mutate(attachment.id)}
                      disabled={deleteMutation.isPending}
                    >
                      Remove
                    </Button>
                  )
                }
              >
                <ListItemText
                  primary={
                    <a
                      href={`${BASE_URL}/evidence/download/${attachment.id}`}
                      target="_blank"
                      rel="noreferrer"
                    >
                      {attachment.filename}
                    </a>
                  }
                />
              </ListItem>
            ))}
          </List>
        )}
      </Paper>
    </Stack>
  );
}

export default CorrespondenceDetailPage;
