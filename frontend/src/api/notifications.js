import { apiRequest } from "./client";

// The alert stream both engines write into. Ordered worst-first by the
// server, so the client never has to re-derive severity ranking.

export function getNotifications({
  projectId,
  unreadOnly = false,
  category,
  limit = 50,
} = {}) {
  const params = new URLSearchParams();
  if (projectId) params.set("project_id", projectId);
  if (unreadOnly) params.set("unread_only", "true");
  if (category) params.set("category", category);
  params.set("limit", String(limit));
  return apiRequest(`/notifications/?${params.toString()}`);
}

export function getNotificationSummary(projectId) {
  const query = projectId ? `?project_id=${projectId}` : "";
  return apiRequest(`/notifications/summary${query}`);
}

export function markNotificationRead(notificationId) {
  return apiRequest(`/notifications/${notificationId}/read`, {
    method: "PATCH",
  });
}

export function markAllNotificationsRead(projectId) {
  const query = projectId ? `?project_id=${projectId}` : "";
  return apiRequest(`/notifications/read-all${query}`, { method: "PATCH" });
}
