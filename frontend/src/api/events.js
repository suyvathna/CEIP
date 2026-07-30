import { apiRequest } from "./client";

export function getProjectEvents(projectId) {
  return apiRequest(`/events/project/${projectId}`);
}

export function getEvent(eventId) {
  return apiRequest(`/events/${eventId}`);
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