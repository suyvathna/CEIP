import { apiRequest } from "./client";

// Clause 13 Variations, and the Sub-Clause 3.5 instructions that might
// be one.

export function getVariationOriginOptions(projectId) {
  const query = projectId ? `?project_id=${projectId}` : "";
  return apiRequest(`/variations/origin-options${query}`);
}

export function getProjectVariations(projectId) {
  return apiRequest(`/variations/project/${projectId}`);
}

export function getVariation(variationId) {
  return apiRequest(`/variations/${variationId}`);
}

export function createVariation(data) {
  return apiRequest("/variations/", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function updateVariation(variationId, data) {
  return apiRequest(`/variations/${variationId}`, {
    method: "PUT",
    body: JSON.stringify(data),
  });
}

// The Sub-Clause 3.5 Notice that the Contractor considers an instruction
// a Variation. Accepted by the API even when late - the clock decides
// whether it was in time, and a late Notice on the record is worth more
// than none.
export function giveVariationNotice(variationId, data) {
  return apiRequest(`/variations/${variationId}/notice`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export function submitVariationProposal(variationId, data) {
  return apiRequest(`/variations/${variationId}/proposal`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export function recordVariationValuation(variationId, data) {
  return apiRequest(`/variations/${variationId}/valuation`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}
