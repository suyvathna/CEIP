import { useParams, useSearchParams, Link as RouterLink } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import Typography from "@mui/material/Typography";
import Stack from "@mui/material/Stack";
import Paper from "@mui/material/Paper";
import Button from "@mui/material/Button";
import Chip from "@mui/material/Chip";
import Tabs from "@mui/material/Tabs";
import Tab from "@mui/material/Tab";
import Alert from "@mui/material/Alert";
import CircularProgress from "@mui/material/CircularProgress";
import List from "@mui/material/List";
import ListItemButton from "@mui/material/ListItemButton";
import ListItemText from "@mui/material/ListItemText";
import AddIcon from "@mui/icons-material/Add";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import { getProjectClaims } from "../api/claims";
import { getProjectVariations } from "../api/variations";
import { getProjectDeterminations } from "../api/determinations";
import ProjectNav from "../components/ProjectNav";
import EngineChip from "../components/EngineChip";
import { ENGINE_B } from "../utils/engines";
import {
  DETERMINATION_STATUS_COLORS,
  DETERMINATION_STATUS_LABELS,
} from "../utils/determination";

const CLAIM_STATUS_COLORS = {
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

const CLAIM_STATUS_LABELS = {
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

const VARIATION_STATUS_COLORS = {
  Logged: "warning",
  NoticeGiven: "info",
  ProposalDue: "warning",
  ProposalSubmitted: "info",
  Instructed: "primary",
  Valued: "success",
  Disputed: "error",
  Rejected: "default",
  Withdrawn: "default",
};

const VARIATION_STATUS_LABELS = {
  Logged: "Logged — no Notice yet",
  NoticeGiven: "Sub-Clause 3.5 Notice given",
  ProposalDue: "Proposal due",
  ProposalSubmitted: "Proposal submitted",
  Instructed: "Instructed as a Variation",
  Valued: "Valued",
  Disputed: "Disputed — pursue as a claim",
  Rejected: "Rejected",
  Withdrawn: "Withdrawn",
};

const ORIGIN_LABELS = {
  EngineerInstruction: "Engineer's Instruction (labelled a Variation)",
  RequestForProposal: "Request for proposal (13.3.2)",
  ValueEngineering: "Contractor's proposal (13.2)",
  UnlabelledInstruction: "Instruction NOT called a Variation",
  Constructive: "Constructive — no instruction issued",
};

const DISGUISED = ["UnlabelledInstruction", "Constructive"];

function ClaimsPanel({ projectId }) {
  const claimsQuery = useQuery({
    queryKey: ["claims", projectId],
    queryFn: () => getProjectClaims(projectId),
  });

  return (
    <Stack spacing={2}>
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
                    <Stack direction="row" spacing={1} sx={{ alignItems: "center", flexWrap: "wrap" }}>
                      {claim.claim_no && (
                        <Chip size="small" variant="outlined" color="primary" label={claim.claim_no} />
                      )}
                      <Typography variant="body1" fontWeight={600}>
                        {claim.title}
                      </Typography>
                      <Chip
                        size="small"
                        label={CLAIM_STATUS_LABELS[claim.status] || claim.status}
                        color={CLAIM_STATUS_COLORS[claim.status] || "default"}
                      />
                      <Chip size="small" variant="outlined" label={claim.claim_type} />
                    </Stack>
                  }
                  secondary={`${claim.claiming_party} — aware since ${claim.awareness_date}${
                    claim.governing_clause ? ` — ${claim.governing_clause}` : ""
                  }${claim.claimed_days ? ` — claiming ${claim.claimed_days} days` : ""}`}
                />
              </ListItemButton>
            ))}
          </List>
        </Paper>
      )}
    </Stack>
  );
}

function VariationsPanel({ projectId }) {
  const variationsQuery = useQuery({
    queryKey: ["variations", projectId],
    queryFn: () => getProjectVariations(projectId),
  });

  const variations = variationsQuery.data || [];
  const exposed = variations.filter(
    (v) => DISGUISED.includes(v.origin) && !v.notice_given_date
  );

  return (
    <Stack spacing={2}>
      <Typography variant="body2" color="text.secondary">
        Clause 13 Variations, and — more to the point — the register of
        instructions that might be one. Engineers change the Works
        constantly without writing the word Variation anywhere: a
        marked-up drawing, a site memo, a line in minutes of meeting.
        Sub-Clause 3.5 requires Notice immediately and before any related
        work starts, so a Contractor who simply builds what was asked and
        raises it at the next valuation has already lost the argument.
      </Typography>

      {exposed.length > 0 && (
        <Alert severity="error">
          <Typography variant="body2" fontWeight={600}>
            {exposed.length} instruction(s) with no Sub-Clause 3.5 Notice
            given.
          </Typography>
          <Typography variant="body2">
            Each of these changes the Works but was not issued as a
            Variation. Give Notice before work on them begins — after that
            the argument gets very much harder to run.
          </Typography>
        </Alert>
      )}

      {variationsQuery.isLoading && <CircularProgress size={24} />}
      {variationsQuery.isError && (
        <Alert severity="error">{variationsQuery.error.message}</Alert>
      )}

      {variationsQuery.data && variations.length === 0 && (
        <Paper sx={{ p: 3 }}>
          <Typography color="text.secondary">
            Nothing logged yet. Log every instruction that changes the
            Works, including the ones that don&apos;t call themselves
            Variations — those are the ones with the immediate notice
            requirement.
          </Typography>
        </Paper>
      )}

      {variations.length > 0 && (
        <Paper>
          <List disablePadding>
            {variations.map((variation) => {
              const disguised = DISGUISED.includes(variation.origin);
              const exposedNow = disguised && !variation.notice_given_date;

              return (
                <ListItemButton
                  key={variation.id}
                  component={RouterLink}
                  to={`/projects/${projectId}/variations/${variation.id}`}
                  divider
                >
                  <ListItemText
                    primary={
                      <Stack
                        direction="row"
                        spacing={1}
                        sx={{ alignItems: "center", flexWrap: "wrap" }}
                      >
                        {variation.variation_no && (
                          <Chip
                            size="small"
                            variant="outlined"
                            color="primary"
                            label={variation.variation_no}
                          />
                        )}
                        <Typography variant="body1" fontWeight={600}>
                          {variation.title}
                        </Typography>
                        <Chip
                          size="small"
                          color={VARIATION_STATUS_COLORS[variation.status] || "default"}
                          label={VARIATION_STATUS_LABELS[variation.status] || variation.status}
                        />
                        {exposedNow && (
                          <Chip
                            size="small"
                            color="error"
                            label="3.5 Notice outstanding"
                          />
                        )}
                        {variation.work_commenced && !variation.notice_given_date && (
                          <Chip
                            size="small"
                            color="error"
                            variant="outlined"
                            label="Work already started"
                          />
                        )}
                      </Stack>
                    }
                    secondary={`${
                      ORIGIN_LABELS[variation.origin] || variation.origin
                    }${
                      variation.instruction_reference
                        ? ` — ref ${variation.instruction_reference}`
                        : ""
                    }${
                      variation.instruction_received_date
                        ? ` — received ${variation.instruction_received_date}`
                        : ""
                    }`}
                  />
                </ListItemButton>
              );
            })}
          </List>
        </Paper>
      )}
    </Stack>
  );
}

function DeterminationsPanel({ projectId }) {
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

const TAB_META = {
  claims: { label: "Claims", newLabel: "New Claim", newTo: "claims/new" },
  variations: { label: "Variations", newLabel: "Log instruction", newTo: "variations/new" },
  determinations: { label: "Determinations", newLabel: null, newTo: null },
};

function ClaimListPage() {
  const { projectId } = useParams();
  const [searchParams, setSearchParams] = useSearchParams();
  const activeTab = TAB_META[searchParams.get("tab")] ? searchParams.get("tab") : "claims";

  function handleTabChange(_, value) {
    const next = new URLSearchParams(searchParams);
    if (value === "claims") {
      next.delete("tab");
    } else {
      next.set("tab", value);
    }
    setSearchParams(next);
  }

  const meta = TAB_META[activeTab];

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
        sx={{ justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 1 }}
      >
        <Stack direction="row" spacing={1.5} sx={{ alignItems: "center", flexWrap: "wrap" }}>
          <Typography variant="h4" fontWeight={700}>
            Claims
          </Typography>
          {activeTab !== "claims" && <EngineChip engine={ENGINE_B} short={false} />}
        </Stack>
        {meta.newTo && (
          <Button
            component={RouterLink}
            to={`/projects/${projectId}/${meta.newTo}`}
            startIcon={<AddIcon fontSize="small" />}
            variant="contained"
          >
            {meta.newLabel}
          </Button>
        )}
      </Stack>

      <Tabs value={activeTab} onChange={handleTabChange} sx={{ borderBottom: 1, borderColor: "divider" }}>
        <Tab value="claims" label="Claims" />
        <Tab value="variations" label="Variations" />
        <Tab value="determinations" label="Determinations" />
      </Tabs>

      {activeTab === "claims" && <ClaimsPanel projectId={projectId} />}
      {activeTab === "variations" && <VariationsPanel projectId={projectId} />}
      {activeTab === "determinations" && <DeterminationsPanel projectId={projectId} />}
    </Stack>
  );
}

export default ClaimListPage;
