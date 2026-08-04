import { Routes, Route } from "react-router-dom";
import Layout from "./components/Layout";
import ProtectedRoute from "./components/ProtectedRoute";
import ProjectListPage from "./pages/ProjectListPage";
import ProjectDetailPage from "./pages/ProjectDetailPage";
import NewProjectPage from "./pages/NewProjectPage";
import EditProjectPage from "./pages/EditProjectPage";
import NewEventPage from "./pages/NewEventPage";
import EventDetailPage from "./pages/EventDetailPage";
import NewDailyLogPage from "./pages/NewDailyLogPage";
import DailyLogDetailPage from "./pages/DailyLogDetailPage";
import NewEvidencePage from "./pages/NewEvidencePage";
import LoginPage from "./pages/LoginPage";
import DeadlinesDashboardPage from "./pages/DeadlinesDashboardPage";
import EditEventPage from "./pages/EditEventPage";
import RegisterPage from "./pages/RegisterPage";
import ProjectReportPage from "./pages/ProjectReportPage";
import SearchResultsPage from "./pages/SearchResultsPage";
import EventRedirectPage from "./pages/EventRedirectPage";
import DailyLogRedirectPage from "./pages/DailyLogRedirectPage";
import ClaimListPage from "./pages/ClaimListPage";
import NewClaimPage from "./pages/NewClaimPage";
import ClaimDetailPage from "./pages/ClaimDetailPage";
import CompliancePage from "./pages/CompliancePage";
import NewVariationPage from "./pages/NewVariationPage";
import VariationDetailPage from "./pages/VariationDetailPage";
import DeterminationDetailPage from "./pages/DeterminationDetailPage";
import CorrespondencePage from "./pages/CorrespondencePage";
import NewCorrespondencePage from "./pages/NewCorrespondencePage";
import CorrespondenceDetailPage from "./pages/CorrespondenceDetailPage";

function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        {/* No /review route here on purpose - CEIP is Contractor-only.
            The Engineer's entire path into a claim is a share link that
            resolves straight to a PDF from the API itself (see
            api/claimAccess.js), never a page of this app. */}
        <Route element={<ProtectedRoute />}>
          <Route path="/deadlines" element={<DeadlinesDashboardPage />} />
          <Route path="/search" element={<SearchResultsPage />} />
          <Route path="/events/:eventId" element={<EventRedirectPage />} />
          <Route path="/daily-logs/:dailyLogId" element={<DailyLogRedirectPage />} />
          <Route path="/" element={<ProjectListPage />} />
          <Route path="/projects/new" element={<NewProjectPage />} />
          <Route path="/projects/:projectId" element={<ProjectDetailPage />} />
          <Route path="/projects/:projectId/edit" element={<EditProjectPage />} />
          <Route path="/projects/:projectId/report" element={<ProjectReportPage />} />

          {/* Engine A - the "ALWAYS DO" compliance register. The engines'
              alerts link straight into these paths, so they have to match
              the link_path values notification_service builds. */}
          <Route path="/projects/:projectId/compliance" element={<CompliancePage />} />

          {/* Variations and Determinations no longer have their own top-
              level nav tab - they're sub-tabs of Claims (?tab=variations /
              ?tab=determinations, see ClaimListPage) - but their new/detail
              routes stay live because notification deep-links point
              straight at a specific record. */}
          <Route path="/projects/:projectId/claims" element={<ClaimListPage />} />
          <Route path="/projects/:projectId/claims/new" element={<NewClaimPage />} />
          <Route path="/projects/:projectId/claims/:claimId" element={<ClaimDetailPage />} />

          {/* Engine B - Clause 13 Variations and the Sub-Clause 3.5
              instructions that might be one. */}
          <Route path="/projects/:projectId/variations/new" element={<NewVariationPage />} />
          <Route path="/projects/:projectId/variations/:variationId" element={<VariationDetailPage />} />

          {/* Engine B - Sub-Clause 3.7 agreements/determinations and the
              28-day Notice of Dissatisfaction window. */}
          <Route path="/projects/:projectId/determinations/:determinationId" element={<DeterminationDetailPage />} />

          {/* Correspondence sent to / received from the Engineer outside
              this platform (email, letter) - just a register, no clock. */}
          <Route path="/projects/:projectId/correspondence" element={<CorrespondencePage />} />
          <Route path="/projects/:projectId/correspondence/new" element={<NewCorrespondencePage />} />
          <Route path="/projects/:projectId/correspondence/:correspondenceId" element={<CorrespondenceDetailPage />} />
          <Route path="/projects/:projectId/correspondence/:correspondenceId/evidence/new" element={<NewEvidencePage />} />

          <Route path="/projects/:projectId/daily-log/new" element={<NewDailyLogPage />} />
          <Route path="/projects/:projectId/daily-log/:dailyLogId" element={<DailyLogDetailPage />} />
          <Route path="/projects/:projectId/daily-log/:dailyLogId/edit" element={<NewDailyLogPage />} />
          <Route path="/projects/:projectId/daily-log/:dailyLogId/evidence/new" element={<NewEvidencePage />} />
          <Route path="/projects/:projectId/events/new" element={<NewEventPage />} />
          <Route path="/projects/:projectId/events/:eventId" element={<EventDetailPage />} />
          <Route path="/projects/:projectId/events/:eventId/edit" element={<EditEventPage />} />
          <Route path="/projects/:projectId/events/:eventId/daily-log/new" element={<NewDailyLogPage />} />
          <Route path="/projects/:projectId/events/:eventId/evidence/new" element={<NewEvidencePage />} />
        </Route>
      </Route>
    </Routes>
  );
}

export default App;
