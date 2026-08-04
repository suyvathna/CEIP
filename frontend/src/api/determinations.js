import { apiRequest } from "./client";

// FIDIC Sub-Clause 3.7 - Agreement or Determination, and the 28-day
// Notice of Dissatisfaction window that follows it.

export function getProjectDeterminations(projectId) {
  return apiRequest(`/determinations/project/${projectId}`);
}

export function getDetermination(determinationId) {
  return apiRequest(`/determinations/${determinationId}`);
}

// Returns null where the claim hasn't reached Sub-Clause 3.7 yet - a
// claim only gets a determination record once its fully detailed claim
// has gone in.
export function getClaimDetermination(claimId) {
  return apiRequest(`/determinations/claim/${claimId}`);
}

// For matters that are NOT Sub-Clause 20.2 claims - valuation disputes,
// measurement disagreements, rate adjustments. Claim-linked
// determinations are opened automatically by the backend when the fully
// detailed claim is submitted.
export function createDetermination(data) {
  return apiRequest("/determinations/", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function updateDetermination(determinationId, data) {
  return apiRequest(`/determinations/${determinationId}`, {
    method: "PUT",
    body: JSON.stringify(data),
  });
}

export function recordAgreement(determinationId, data) {
  return apiRequest(`/determinations/${determinationId}/agreement`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

// The 28-day NOD clock runs from determination_received_date, not from
// the date printed on the Engineer's letter, which is why the form
// captures both.
export function recordDeterminationReceived(determinationId, data) {
  return apiRequest(`/determinations/${determinationId}/received`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export function giveNoticeOfDissatisfaction(determinationId, data) {
  return apiRequest(`/determinations/${determinationId}/nod`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}
