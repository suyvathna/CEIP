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

function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/login" element={<LoginPage />} />

        <Route element={<ProtectedRoute />}>
          <Route path="/deadlines" element={<DeadlinesDashboardPage />} />
          <Route path="/" element={<ProjectListPage />} />
          <Route path="/projects/new" element={<NewProjectPage />} />
          <Route path="/projects/:projectId" element={<ProjectDetailPage />} />
          <Route path="/projects/:projectId/edit" element={<EditProjectPage />} />
          <Route path="/projects/:projectId/events/new" element={<NewEventPage />} />
          <Route path="/projects/:projectId/events/:eventId" element={<EventDetailPage />} />
          <Route path="/projects/:projectId/events/:eventId/diary/new" element={<NewDiaryPage />} />
          <Route path="/projects/:projectId/events/:eventId/evidence/new" element={<NewEvidencePage />} />
        </Route>
      </Route>
    </Routes>
  );
}

export default App;