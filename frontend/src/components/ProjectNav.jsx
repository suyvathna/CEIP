import { Link as RouterLink } from "react-router-dom";
import Tabs from "@mui/material/Tabs";
import Tab from "@mui/material/Tab";
import Box from "@mui/material/Box";
import SummarizeIcon from "@mui/icons-material/Summarize";
import InfoOutlinedIcon from "@mui/icons-material/InfoOutlined";
import ScheduleIcon from "@mui/icons-material/Schedule";
import GavelIcon from "@mui/icons-material/Gavel";
import FactCheckIcon from "@mui/icons-material/FactCheck";
import ForwardToInboxIcon from "@mui/icons-material/ForwardToInbox";

/**
 * Shared tab strip for the project-scoped screens. Each screen is its own
 * route, so navigation happens via plain router links rather than in-page
 * tab switching.
 *
 * Order follows the shape of the contract rather than the order the
 * screens were built: what's coming up next (Deadlines, right alongside
 * Overview), what the calendar requires (Compliance), what is being
 * claimed (Claims — which now also holds Variations and Determinations as
 * sub-tabs), what was sent to/received from the Engineer outside this
 * platform (Correspondence), and the exportable record of it all - the
 * Events/Daily Log registers plus the export panels (Site Records).
 *
 * Every screen reachable from here is scoped to this one project - there
 * is no cross-project view anywhere in the app, Deadlines included.
 */
function ProjectNav({ projectId, active }) {
  return (
    <Box sx={{ borderBottom: 1, borderColor: "divider", mb: 3 }}>
      {/* MUI wants `false`, not undefined/null, for "no tab selected" -
          used on screens like Search that aren't one of the fixed
          sections below. */}
      <Tabs value={active || false} variant="scrollable" scrollButtons="auto">
        <Tab
          value="overview"
          label="Overview"
          icon={<InfoOutlinedIcon fontSize="small" />}
          iconPosition="start"
          component={RouterLink}
          to={`/projects/${projectId}`}
        />
        <Tab
          value="deadlines"
          label="Deadlines"
          icon={<ScheduleIcon fontSize="small" />}
          iconPosition="start"
          component={RouterLink}
          to={`/projects/${projectId}/deadlines`}
        />
        <Tab
          value="compliance"
          label="Compliance"
          icon={<FactCheckIcon fontSize="small" />}
          iconPosition="start"
          component={RouterLink}
          to={`/projects/${projectId}/compliance`}
        />
        <Tab
          value="claims"
          label="Claims"
          icon={<GavelIcon fontSize="small" />}
          iconPosition="start"
          component={RouterLink}
          to={`/projects/${projectId}/claims`}
        />
        <Tab
          value="correspondence"
          label="Correspondence"
          icon={<ForwardToInboxIcon fontSize="small" />}
          iconPosition="start"
          component={RouterLink}
          to={`/projects/${projectId}/correspondence`}
        />
        <Tab
          value="report"
          label="Site Records"
          icon={<SummarizeIcon fontSize="small" />}
          iconPosition="start"
          component={RouterLink}
          to={`/projects/${projectId}/report`}
        />
      </Tabs>
    </Box>
  );
}

export default ProjectNav;
