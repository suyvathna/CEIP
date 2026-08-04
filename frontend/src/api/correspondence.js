import { apiRequest } from "./client";

export function getProjectCorrespondence(projectId) {
  return apiRequest(`/correspondence/project/${projectId}`);
}

export function getCorrespondence(correspondenceId) {
  return apiRequest(`/correspondence/${correspondenceId}`);
}

export function createCorrespondence(data) {
  return apiRequest("/correspondence/", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function updateCorrespondence(correspondenceId, data) {
  return apiRequest(`/correspondence/${correspondenceId}`, {
    method: "PUT",
    body: JSON.stringify(data),
  });
}

export function deleteCorrespondence(correspondenceId) {
  return apiRequest(`/correspondence/${correspondenceId}`, {
    method: "DELETE",
  });
}
