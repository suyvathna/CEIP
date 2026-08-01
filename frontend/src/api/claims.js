import { apiRequest, BASE_URL, getToken } from "./client";

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

export function getClaimDailyLogs(claimId) {
  return apiRequest(`/claims/${claimId}/daily-logs`);
}

export function linkClaimDailyLog(claimId, dailyLogId) {
  return apiRequest(`/claims/${claimId}/daily-logs`, {
    method: "POST",
    body: JSON.stringify({ daily_log_id: dailyLogId }),
  });
}

export function unlinkClaimDailyLog(claimId, dailyLogId) {
  return apiRequest(`/claims/${claimId}/daily-logs/${dailyLogId}`, {
    method: "DELETE",
  });
}

export function getClaimEvidenceList(claimId) {
  return apiRequest(`/claims/${claimId}/evidence`);
}

export function linkClaimEvidence(claimId, evidenceId) {
  return apiRequest(`/claims/${claimId}/evidence`, {
    method: "POST",
    body: JSON.stringify({ evidence_id: evidenceId }),
  });
}

export function unlinkClaimEvidence(claimId, evidenceId) {
  return apiRequest(`/claims/${claimId}/evidence/${evidenceId}`, {
    method: "DELETE",
  });
}

export function getClaimRequirements(claimId) {
  return apiRequest(`/claims/${claimId}/requirements`);
}

export function getEngineerDetermination(claimId) {
  return apiRequest(`/claims/${claimId}/engineer-determination`);
}

export function getClaimClauseOptions() {
  return apiRequest("/claims/clause-options");
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

// Downloads the same read-only claim PDF a share link would hand the
// Engineer, but straight from the Contractor's own logged-in session -
// for printing or attaching to an email/Telegram message by hand. Not
// routed through apiRequest, since that always parses JSON; a PDF needs
// to come back as a blob instead.
export async function downloadClaimReportPdf(claimId) {
  const token = getToken();
  const response = await fetch(`${BASE_URL}/claims/${claimId}/report/pdf`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });

  if (!response.ok) {
    throw new Error("Could not generate the claim report PDF.");
  }

  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `claim-report-${claimId}.pdf`;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
}
