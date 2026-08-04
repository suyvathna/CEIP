import { apiRequest } from "./client";

export function getProjectEvents(projectId) {
  return apiRequest(`/events/project/${projectId}`);
}

export function getEvent(eventId) {
  return apiRequest(`/events/${eventId}`);
}

export function getEventRequirements(eventId) {
  return apiRequest(`/events/${eventId}/requirements`);
}

export function createEvent(data) {
  return apiRequest("/events/", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function markNoticeGiven(eventId, noticeGivenDate) {
  return apiRequest(`/events/${eventId}/notice`, {
    method: "PATCH",
    body: JSON.stringify({ notice_given_date: noticeGivenDate }),
  });
}

export function getAllEvents() {
  return apiRequest("/events/filter");
}

export function updateEvent(eventId, data) {
  return apiRequest(`/events/${eventId}`, {
    method: "PUT",
    body: JSON.stringify(data),
  });
}

export function deleteEvent(eventId) {
  return apiRequest(`/events/${eventId}`, {
    method: "DELETE",
  });
}

export function filterEvents({ projectId, eventType, severity, status } = {}) {
  const params = new URLSearchParams();

  if (projectId) params.set("project_id", projectId);
  if (eventType) params.set("event_type", eventType);
  if (severity) params.set("severity", severity);
  if (status) params.set("status", status);

  const query = params.toString();
  return apiRequest(`/events/filter${query ? `?${query}` : ""}`);
}

export function searchEvents(keyword) {
  return apiRequest(`/events/search?keyword=${encodeURIComponent(keyword)}`);
}

export function searchEventsByDate(startDate, endDate) {
  return apiRequest(
    `/events/search-by-date?start_date=${startDate}&end_date=${endDate}`
  );
}