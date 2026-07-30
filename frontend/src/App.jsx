import { Routes, Route } from "react-router-dom";
import ProjectListPage from "./pages/ProjectListPage";
import ProjectDetailPage from "./pages/ProjectDetailPage";
import NewProjectPage from "./pages/NewProjectPage";
import NewEventPage from "./pages/NewEventPage";

function App() {
  return (
    <Routes>
      <Route path="/" element={<ProjectListPage />} />
      <Route path="/projects/new" element={<NewProjectPage />} />
      <Route path="/projects/:projectId" element={<ProjectDetailPage />} />
      <Route path="/projects/:projectId/events/new" element={<NewEventPage />} />
    </Routes>
  );
}

export default App;