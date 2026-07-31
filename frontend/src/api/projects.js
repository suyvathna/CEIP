import { apiRequest } from "./client";

export function getProjects() {
  return apiRequest("/projects/");
}

export function getProject(projectId) {
  return apiRequest(`/projects/${projectId}`);
}

export function createProject(data) {
  return apiRequest("/projects/", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function updateProject(projectId, data) {
  return apiRequest(`/projects/${projectId}`, {
    method: "PUT",
    body: JSON.stringify(data),
  });
}

export function deleteProject(projectId) {
  return apiRequest(`/projects/${projectId}`, {
    method: "DELETE",
  });
}

// Manually mark a project Completed or On Hold, or resume one back to
// auto (date-driven) status with "In Progress". Separate from the plain
// PUT above since this is a one-field workflow action, not an edit of
// the project's own details.
export function updateProjectStatus(projectId, status) {
  return apiRequest(`/projects/${projectId}/status`, {
    method: "PATCH",
    body: JSON.stringify({ status }),
  });
}