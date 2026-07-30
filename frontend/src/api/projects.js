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