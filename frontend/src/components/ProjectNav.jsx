import { Link as RouterLink } from "react-router-dom";
import Tabs from "@mui/material/Tabs";
import Tab from "@mui/material/Tab";
import Box from "@mui/material/Box";
import DashboardIcon from "@mui/icons-material/Dashboard";
import TimelineIcon from "@mui/icons-material/Timeline";
import SummarizeIcon from "@mui/icons-material/Summarize";
import InfoOutlinedIcon from "@mui/icons-material/InfoOutlined";
import GavelIcon from "@mui/icons-material/Gavel";
import AccountTreeIcon from "@mui/icons-material/AccountTree";
import FactCheckIcon from "@mui/icons-material/FactCheck";
import EditNoteIcon from "@mui/icons-material/EditNote";
import BalanceIcon from "@mui/icons-material/Balance";

/**
 * Shared tab strip for the project-scoped screens. Each screen is its own
 * route, so navigation happens via plain router links rather than in-page
 * tab switching.
 *
 * Order follows the shape of the contract rather than the order the
 * screens were built: what the calendar requires (Compliance), what the
 * site recorded (Timeline), what is being claimed (Claims), what was
 * instructed (Variations), and what the Engineer has decided
 * (Determinations).
 */
function ProjectNav({ projectId, active }) {
  return (
    <Box sx={{ borderBottom: 1, borderColor: "divider", mb: 3 }}>
      <Tabs value={active} variant="scrollable" scrollButtons="auto">
        <Tab
          value="overview"
          label="Overview"
          icon={<InfoOutlinedIcon fontSize="small" />}
          iconPosition="start"
          component={RouterLink}
          to={`/projects/${projectId}`}
        />
        <Tab
          value="dashboard"
          label="Dashboard"
          icon={<DashboardIcon fontSize="small" />}
          iconPosition="start"
          component={RouterLink}
          to={`/projects/${projectId}/dashboard`}
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
          value="timeline"
          label="Timeline"
          icon={<TimelineIcon fontSize="small" />}
          iconPosition="start"
          component={RouterLink}
          to={`/projects/${projectId}/timeline`}
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
          value="variations"
          label="Variations"
          icon={<EditNoteIcon fontSize="small" />}
          iconPosition="start"
          component={RouterLink}
          to={`/projects/${projectId}/variations`}
        />
        <Tab
          value="determinations"
          label="Determinations"
          icon={<BalanceIcon fontSize="small" />}
          iconPosition="start"
          component={RouterLink}
          to={`/projects/${projectId}/determinations`}
        />
        <Tab
          value="programme"
          label="Programme"
          icon={<AccountTreeIcon fontSize="small" />}
          iconPosition="start"
          component={RouterLink}
          to={`/projects/${projectId}/programme`}
        />
        <Tab
          value="report"
          label="Report"
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
