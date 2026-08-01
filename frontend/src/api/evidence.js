import { apiRequest } from "./client";

// owner is { eventId } or { dailyLogId } - exactly one. category/caption
// are optional and mainly useful for Daily Log photos (bucketing a photo
// into a section, e.g. "Delivery" or "HSE" - the same field a future
// camera-API import would set automatically).
export function uploadEvidence(owner, file, { category, caption } = {}) {
  const formData = new FormData();
  if (owner.eventId) formData.append("event_id", owner.eventId);
  if (owner.dailyLogId) formData.append("daily_log_id", owner.dailyLogId);
  if (category) formData.append("category", category);
  if (caption) formData.append("caption", caption);
  formData.append("file", file);

  return apiRequest("/evidence/upload", {
    method: "POST",
    body: formData,
  });
}

export function getEventEvidence(eventId) {
  return apiRequest(`/evidence/search?event_id=${eventId}`);
}

export function getDailyLogEvidence(dailyLogId) {
  return apiRequest(`/evidence/search?daily_log_id=${dailyLogId}`);
}

export function getEvidence(evidenceId) {
  return apiRequest(`/evidence/${evidenceId}`);
}

export function deleteEvidence(evidenceId) {
  return apiRequest(`/evidence/${evidenceId}`, {
    method: "DELETE",
  });
}
