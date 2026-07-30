import { apiRequest } from "./client";

// These hit the /public/claims/{token} routes, which deliberately require
// no authentication - this is the Engineer's no-account-needed path into
// a single claim (see the magic-link access feature).

export function getPublicClaimOverview(token) {
  return apiRequest(`/public/claims/${token}`);
}

export function respondToPublicFact(token, factId, data) {
  return apiRequest(`/public/claims/${token}/facts/${factId}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export function submitPublicEngineerResponse(token, data) {
  return apiRequest(`/public/claims/${token}/response`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}
