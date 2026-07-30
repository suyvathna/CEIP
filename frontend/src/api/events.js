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