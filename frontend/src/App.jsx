import { Routes, Route } from "react-router-dom";
import Layout from "./components/Layout";
import ProtectedRoute from "./components/ProtectedRoute";
import ProjectListPage from "./pages/ProjectListPage";
import ProjectDetailPage from "./pages/ProjectDetailPage";
import NewProjectPage from "./pages/NewProjectPage";
import EditProjectPage from "./pages/EditProjectPage";
import NewEventPage from "./pages/NewEventPage";
import EventDetailPage from "./pages/EventDetailPage";
import NewDiaryPage from "./pages/NewDiaryPage";
import NewEvidencePage from "./pages/NewEvidencePage";
import LoginPage from "./pages/LoginPage";
import DeadlinesDashboardPage from "./pages/DeadlinesDashboardPage";
import EditEventPage from "./pages/EditEventPage";
import RegisterPage from "./pages/RegisterPage";
import DashboardPage from "./pages/DashboardPage";
import TimelinePage from "./pages/TimelinePage";
import ProjectReportPage from "./pages/ProjectReportPage";
import SearchResultsPage from "./pages/SearchResultsPage";
import EventRedirectPage from "./pages/EventRedirectPage";
import DiaryRedirectPage from "./pages/DiaryRedirectPage";

function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route element={<ProtectedRoute />}>
          <Route path="/deadlines" element={<DeadlinesDashboardPage />} />
          <Route path="/search" element={<SearchResultsPage />} />
          <Route path="/events/:eventId" element={<EventRedirectPage />} />
          <Route path="/diaries/:diaryId" element={<DiaryRedirectPage />} />
          <Route path="/" element={<ProjectListPage />} />
          <Route path="/projects/new" element={<NewProjectPage />} />
          <Route path="/projects/:projectId" element={<ProjectDetailPage />} />
          <Route path="/projects/:projectId/edit" element={<EditProjectPage />} />
          <Route path="/projects/:projectId/dashboard" element={<DashboardPage />} />
          <Route path="/projects/:projectId/timeline" element={<TimelinePage />} />
          <Route path="/projects/:projectId/report" element={<ProjectReportPage />} />
          <Route path="/projects/:projectId/events/new" element={<NewEventPage />} />
          <Route path="/projects/:projectId/events/:eventId" element={<EventDetailPage />} />
          <Route path="/projects/:projectId/events/:eventId/edit" element={<EditEventPage />} />
          <Route path="/projects/:projectId/events/:eventId/diary/new" element={<NewDiaryPage />} />
          <Route path="/projects/:projectId/events/:eventId/evidence/new" element={<NewEvidencePage />} />
        </Route>
      </Route>
    </Routes>
  );
}

export default App;
