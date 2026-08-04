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

// Contract milestones and engine periods: Letter of Acceptance,
// Taking-Over Certificate, Performance Certificate, the Defects
// Notification Period, and the Sub-Clause 3.7 / 3.5 / 13.3 windows.
//
// A true PATCH - only the keys sent are written. Deliberately NOT part
// of updateProject above: that endpoint's body is the full ProjectCreate
// schema and the server setattr's every field on it, so a PM editing the
// project's city through the ordinary edit form would blank the
// Taking-Over date and silently retire half the compliance register.
export function updateProjectMilestones(projectId, data) {
  return apiRequest(`/projects/${projectId}/milestones`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}