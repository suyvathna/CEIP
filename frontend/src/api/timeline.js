import { apiRequest } from "./client";

export function getProjectTimeline(projectId, filters = {}) {
  const params = new URLSearchParams();

  if (filters.startDate) params.set("start_date", filters.startDate);
  if (filters.endDate) params.set("end_date", filters.endDate);
  if (filters.eventType) params.set("event_type", filters.eventType);
  if (filters.severity) params.set("severity", filters.severity);

  const query = params.toString();
  return apiRequest(`/timeline/${projectId}${query ? `?${query}` : ""}`);
}

export function getTimelineAnalytics(projectId) {
  return apiRequest(`/events/project/${projectId}/timeline-analytics`);
}

export function getProjectActivity(projectId) {
  return apiRequest(`/events/project/${projectId}/activity`);
}
