import { BASE_URL } from "./client";

// CEIP is Contractor-only - the Engineer never has an account or any
// access to this app. The only thing a share link (created via
// createClaimAccessLink in api/claims.js) can ever resolve to is a
// read-only PDF served directly by the API, so this file just builds
// that URL rather than calling any endpoint of its own. There is no
// frontend page for the Engineer's side of this at all.

export function getPublicClaimReportPdfUrl(token) {
  return `${BASE_URL}/public/claims/${token}/pdf`;
}
