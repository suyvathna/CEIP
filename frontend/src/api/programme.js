import { apiRequest } from "./client";

export function getProjectActivities(projectId) {
  return apiRequest(`/programme/project/${projectId}/activities`);
}

export function createActivity(projectId, data) {
  return apiRequest(`/programme/project/${projectId}/activities`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function updateActivity(activityId, data) {
  return apiRequest(`/programme/activities/${activityId}`, {
    method: "PUT",
    body: JSON.stringify(data),
  });
}

export function deleteActivity(activityId) {
  return apiRequest(`/programme/activities/${activityId}`, {
    method: "DELETE",
  });
}

export function addPredecessor(activityId, predecessorId) {
  return apiRequest(`/programme/activities/${activityId}/predecessors`, {
    method: "POST",
    body: JSON.stringify({ predecessor_id: predecessorId }),
  });
}

export function removePredecessor(activityId, predecessorId) {
  return apiRequest(
    `/programme/activities/${activityId}/predecessors/${predecessorId}`,
    { method: "DELETE" }
  );
}

export function createEventImpact(eventId, data) {
  return apiRequest(`/programme/events/${eventId}/impacts`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function getProjectCPM(projectId) {
  return apiRequest(`/programme/project/${projectId}/cpm`);
}

export function getClaimDelayAnalysis(claimId, projectId) {
  return apiRequest(
    `/programme/claims/${claimId}/delay-analysis?project_id=${projectId}`
  );
}
