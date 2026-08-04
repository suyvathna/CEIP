import Accordion from "@mui/material/Accordion";
import AccordionSummary from "@mui/material/AccordionSummary";
import AccordionDetails from "@mui/material/AccordionDetails";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import Grid from "@mui/material/Grid";
import Paper from "@mui/material/Paper";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import EngineChip from "./EngineChip";
import {
  ENGINE_A,
  ENGINE_B,
  ENGINE_DESCRIPTIONS,
  ENGINE_SCOPE,
} from "../utils/engines";

/**
 * "Which of these is Engine A and which is Engine B?" - answered in the
 * product rather than in a document nobody has open at the time.
 *
 * Collapsed by default so it costs nothing once you know, and it lives
 * on the two screens where the question actually arises: the global
 * Deadlines feed (which mixes both) and the Compliance register (which
 * is pure Engine A and needs to say so).
 */
function EngineExplainer({ defaultExpanded = false }) {
  return (
    <Accordion defaultExpanded={defaultExpanded}>
      <AccordionSummary expandIcon={<ExpandMoreIcon />}>
        <Typography variant="subtitle2">
          What are Engine A and Engine B?
        </Typography>
      </AccordionSummary>

      <AccordionDetails>
        <Grid container spacing={2}>
          {[ENGINE_A, ENGINE_B].map((engine) => (
            <Grid key={engine} size={{ xs: 12, md: 6 }}>
              <Paper variant="outlined" sx={{ p: 2, height: "100%" }}>
                <Stack spacing={1}>
                  <EngineChip engine={engine} short={false} />
                  <Typography variant="body2" color="text.secondary">
                    {ENGINE_DESCRIPTIONS[engine]}
                  </Typography>
                  <Stack component="ul" sx={{ pl: 2, m: 0 }} spacing={0.25}>
                    {ENGINE_SCOPE[engine].map((line) => (
                      <Typography
                        key={line}
                        component="li"
                        variant="caption"
                        color="text.secondary"
                      >
                        {line}
                      </Typography>
                    ))}
                  </Stack>
                </Stack>
              </Paper>
            </Grid>
          ))}
        </Grid>

        <Typography variant="caption" color="text.secondary" sx={{ mt: 2, display: "block" }}>
          The practical difference: an Engine A deadline missed is a
          breach you can usually put right. An Engine B deadline missed is
          usually gone — a Sub-Clause 20.2 notice period, or the 28 days
          to object to the Engineer&apos;s determination, take the
          entitlement with them when they expire.
        </Typography>
      </AccordionDetails>
    </Accordion>
  );
}

export default EngineExplainer;
