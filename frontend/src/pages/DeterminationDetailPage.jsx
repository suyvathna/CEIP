import { useParams, Link as RouterLink } from "react-router-dom";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import Typography from "@mui/material/Typography";
import Stack from "@mui/material/Stack";
import Paper from "@mui/material/Paper";
import Button from "@mui/material/Button";
import Alert from "@mui/material/Alert";
import CircularProgress from "@mui/material/CircularProgress";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import ProjectNav from "../components/ProjectNav";
import { DeterminationBody } from "../components/DeterminationPanel";
import { getDetermination } from "../api/determinations";

function DeterminationDetailPage() {
  const { projectId, determinationId } = useParams();
  const queryClient = useQueryClient();

  const query = useQuery({
    queryKey: ["determination", determinationId],
    queryFn: () => getDetermination(determinationId),
  });

  function handleChanged() {
    queryClient.invalidateQueries({ queryKey: ["determination", determinationId] });
    queryClient.invalidateQueries({ queryKey: ["determinations", projectId] });
    queryClient.invalidateQueries({ queryKey: ["notificationSummary"] });
  }

  if (query.isLoading) return <CircularProgress />;
  if (query.isError) return <Alert severity="error">{query.error.message}</Alert>;

  const { determination, claim_no: claimNo, claim_title: claimTitle } = query.data;

  return (
    <Stack spacing={2}>
      <Button
        component={RouterLink}
        to={`/projects/${projectId}/claims?tab=determinations`}
        size="small"
        startIcon={<ArrowBackIcon fontSize="small" />}
        sx={{ alignSelf: "flex-start" }}
      >
        Back to claims
      </Button>

      <ProjectNav projectId={projectId} active="claims" />

      <Typography variant="h4" fontWeight={700}>
        {determination.matter_title}
      </Typography>

      {determination.claim_id && (
        <Button
          component={RouterLink}
          to={`/projects/${projectId}/claims/${determination.claim_id}`}
          size="small"
          sx={{ alignSelf: "flex-start" }}
        >
          Open the linked claim {claimNo ? `(${claimNo})` : ""}
          {claimTitle ? ` — ${claimTitle}` : ""}
        </Button>
      )}

      {determination.matter_description && (
        <Paper sx={{ p: 3 }}>
          <Typography variant="body2" sx={{ whiteSpace: "pre-wrap" }}>
            {determination.matter_description}
          </Typography>
        </Paper>
      )}

      <DeterminationBody detail={query.data} onChanged={handleChanged} />
    </Stack>
  );
}

export default DeterminationDetailPage;
