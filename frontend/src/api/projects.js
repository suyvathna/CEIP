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