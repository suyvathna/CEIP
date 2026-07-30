import { apiRequest } from "./client";

export function uploadEvidence(eventId, file) {
  const formData = new FormData();
  formData.append("event_id", eventId);
  formData.append("file", file);

  return apiRequest("/evidence/upload", {
    method: "POST",
    body: formData,
  });
}

export function getEventEvidence(eventId) {
  return apiRequest(`/evidence/search?event_id=${eventId}`);
}

export function getEvidence(evidenceId) {
  return apiRequest(`/evidence/${evidenceId}`);
}

export function deleteEvidence(evidenceId) {
  return apiRequest(`/evidence/${evidenceId}`, {
    method: "DELETE",
  });
}