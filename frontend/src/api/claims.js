import { apiRequest } from "./client";

export function getProjectClaims(projectId) {
  return apiRequest(`/claims/project/${projectId}`);
}

export function getClaim(claimId) {
  return apiRequest(`/claims/${claimId}`);
}

export function createClaim(data) {
  return apiRequest("/claims/", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function getClaimClock(claimId) {
  return apiRequest(`/claims/${claimId}/clock`);
}

export function getClaimEvents(claimId) {
  return apiRequest(`/claims/${claimId}/events`);
}

export function linkClaimEvent(claimId, eventId) {
  return apiRequest(`/claims/${claimId}/events`, {
    method: "POST",
    body: JSON.stringify({ event_id: eventId }),
  });
}

export function unlinkClaimEvent(claimId, eventId) {
  return apiRequest(`/claims/${claimId}/events/${eventId}`, {
    method: "DELETE",
  });
}

export function submitClaimNotice(claimId, data) {
  return apiRequest(`/claims/${claimId}/notice`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export function flagClaimLateNotice(claimId, data) {
  return apiRequest(`/claims/${claimId}/engineer-flag`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export function submitDetailedClaim(claimId, data) {
  return apiRequest(`/claims/${claimId}/detailed-claim`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export function submitEngineerResponse(claimId, data) {
  return apiRequest(`/claims/${claimId}/engineer-response`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export function getClaimResponses(claimId) {
  return apiRequest(`/claims/${claimId}/responses`);
}

export function createClaimAccessLink(claimId, recipientEmail, ttlDays = 60) {
  return apiRequest(`/claims/${claimId}/access-links`, {
    method: "POST",
    body: JSON.stringify({ recipient_email: recipientEmail, ttl_days: ttlDays }),
  });
}
