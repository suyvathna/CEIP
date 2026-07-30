import { apiRequest } from "./client";

export function getClaimFacts(claimId) {
  return apiRequest(`/claims/${claimId}/facts`);
}

export function getClaimFactSummary(claimId) {
  return apiRequest(`/claims/${claimId}/facts/summary`);
}

export function createClaimFact(claimId, data) {
  return apiRequest(`/claims/${claimId}/facts`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function respondToFact(factId, data) {
  return apiRequest(`/facts/${factId}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export function linkFactEvidence(factId, evidenceId) {
  return apiRequest(`/facts/${factId}/evidence/${evidenceId}`, {
    method: "POST",
  });
}
