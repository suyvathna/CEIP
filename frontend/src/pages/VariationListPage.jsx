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
import ProjectNav from "../components/ProjectNav";
import EngineChip from "../components/EngineChip";
import { ENGINE_B } from "../utils/engines";
import { getProjectVariations } from "../api/variations";

const STATUS_COLORS = {
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

const STATUS_LABELS = {
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

function VariationListPage() {
  const { projectId } = useParams();

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
      <Button
        component={RouterLink}
        to={`/projects/${projectId}`}
        size="small"
        startIcon={<ArrowBackIcon fontSize="small" />}
        sx={{ alignSelf: "flex-start" }}
      >
        Back to project
      </Button>

      <ProjectNav projectId={projectId} active="variations" />

      <Stack
        direction="row"
        sx={{ justifyContent: "space-between", alignItems: "center" }}
      >
        <Stack direction="row" spacing={1.5} sx={{ alignItems: "center", flexWrap: "wrap" }}>
          <Typography variant="h4" fontWeight={700}>
            Variations &amp; instructions
          </Typography>
          <EngineChip engine={ENGINE_B} short={false} />
        </Stack>
        <Button
          component={RouterLink}
          to={`/projects/${projectId}/variations/new`}
          startIcon={<AddIcon fontSize="small" />}
          variant="contained"
        >
          Log instruction
        </Button>
      </Stack>

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
                          color={STATUS_COLORS[variation.status] || "default"}
                          label={STATUS_LABELS[variation.status] || variation.status}
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

export default VariationListPage;
