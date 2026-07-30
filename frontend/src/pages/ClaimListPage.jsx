import { useParams, Link as RouterLink } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import Typography from "@mui/material/Typography";
import Stack from "@mui/material/Stack";
import Paper from "@mui/material/Paper";
import Button from "@mui/material/Button";
import Chip from "@mui/material/Chip";
import CircularProgress from "@mui/material/CircularProgress";
import Alert from "@mui/material/Alert";
import List from "@mui/material/List";
import ListItemButton from "@mui/material/ListItemButton";
import ListItemText from "@mui/material/ListItemText";
import AddIcon from "@mui/icons-material/Add";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import { getProjectClaims } from "../api/claims";
import ProjectNav from "../components/ProjectNav";

const STATUS_COLORS = {
  Notified: "info",
  NoticeFlaggedLate: "warning",
  DetailedClaimSubmitted: "info",
  AwaitingEngineerResponse: "warning",
  Agreed: "success",
  PartiallyAgreed: "success",
  Determined: "default",
  DeemedRejected: "error",
  ReferredToDAAB: "error",
  Lapsed: "error",
};

const STATUS_LABELS = {
  Notified: "Notified",
  NoticeFlaggedLate: "Notice flagged late",
  DetailedClaimSubmitted: "Detailed claim submitted",
  AwaitingEngineerResponse: "Awaiting Engineer response",
  Agreed: "Agreed",
  PartiallyAgreed: "Partially agreed",
  Determined: "Determined",
  DeemedRejected: "Deemed rejected (no response in time)",
  ReferredToDAAB: "Referred to DAAB",
  Lapsed: "Lapsed (20.2.4 legal basis missing)",
};

function ClaimListPage() {
  const { projectId } = useParams();

  const claimsQuery = useQuery({
    queryKey: ["claims", projectId],
    queryFn: () => getProjectClaims(projectId),
  });

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

      <ProjectNav projectId={projectId} active="claims" />

      <Stack
        direction="row"
        sx={{ justifyContent: "space-between", alignItems: "center" }}
      >
        <Typography variant="h4" fontWeight={700}>
          Claims
        </Typography>
        <Button
          component={RouterLink}
          to={`/projects/${projectId}/claims/new`}
          startIcon={<AddIcon fontSize="small" />}
          variant="contained"
        >
          New Claim
        </Button>
      </Stack>

      {claimsQuery.isLoading && <CircularProgress size={24} />}
      {claimsQuery.isError && (
        <Alert severity="error">{claimsQuery.error.message}</Alert>
      )}

      {claimsQuery.data && claimsQuery.data.length === 0 && (
        <Paper sx={{ p: 3 }}>
          <Typography color="text.secondary">
            No claims recorded yet for this project. A claim ties one or
            more logged events to the Sub-Clause 20.2 notice / fully
            detailed claim / Engineer response process.
          </Typography>
        </Paper>
      )}

      {claimsQuery.data && claimsQuery.data.length > 0 && (
        <Paper>
          <List disablePadding>
            {claimsQuery.data.map((claim) => (
              <ListItemButton
                key={claim.id}
                component={RouterLink}
                to={`/projects/${projectId}/claims/${claim.id}`}
                divider
              >
                <ListItemText
                  primary={
                    <Stack direction="row" spacing={1} sx={{ alignItems: "center" }}>
                      <Typography variant="body1" fontWeight={600}>
                        {claim.title}
                      </Typography>
                      <Chip
                        size="small"
                        label={STATUS_LABELS[claim.status] || claim.status}
                        color={STATUS_COLORS[claim.status] || "default"}
                      />
                      <Chip size="small" variant="outlined" label={claim.claim_type} />
                    </Stack>
                  }
                  secondary={`${claim.claiming_party} — aware since ${claim.awareness_date}${
                    claim.claimed_days ? ` — claiming ${claim.claimed_days} days` : ""
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

export default ClaimListPage;
