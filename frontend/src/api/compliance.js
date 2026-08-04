import { apiRequest } from "./client";

// Engine A - the "ALWAYS DO" compliance register, plus the unified
// deadline feed both engines publish into.

export function getComplianceRules(projectId) {
  const query = projectId ? `?project_id=${projectId}` : "";
  return apiRequest(`/compliance/rules${query}`);
}

export function getEventDrivenRules(projectId) {
  const query = projectId ? `?project_id=${projectId}` : "";
  return apiRequest(`/compliance/event-driven-rules${query}`);
}

export function getComplianceFilters() {
  return apiRequest("/compliance/filters");
}

export function getComplianceRegister(projectId, { status, category } = {}) {
  const params = new URLSearchParams();
  if (status) params.set("status", status);
  if (category) params.set("category", category);
  const query = params.toString() ? `?${params.toString()}` : "";
  return apiRequest(`/compliance/project/${projectId}${query}`);
}

export function regenerateRegister(projectId) {
  return apiRequest(`/compliance/project/${projectId}/regenerate`, {
    method: "POST",
  });
}

export function submitObligation(obligationId, data) {
  return apiRequest(`/compliance/obligations/${obligationId}/submit`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export function waiveObligation(obligationId, reason) {
  return apiRequest(`/compliance/obligations/${obligationId}/waive`, {
    method: "PATCH",
    body: JSON.stringify({ reason }),
  });
}

export function reopenObligation(obligationId) {
  return apiRequest(`/compliance/obligations/${obligationId}/reopen`, {
    method: "PATCH",
  });
}

// One request for every live deadline across both engines - compliance
// obligations, event notice periods, Sub-Clause 20.2 claim stages,
// Sub-Clause 3.7 determinations and Sub-Clause 3.5 instructions.
//
// This replaces the Deadlines page's old approach of fetching every
// project, then every claim, then one clock per claim: roughly fifty
// sequential round trips to render one screen for a contractor running
// eight jobs, and it still couldn't see anything but events and claims.
export function getDeadlineFeed({ projectId, withinDays } = {}) {
  const params = new URLSearchParams();
  if (projectId) params.set("project_id", projectId);
  if (withinDays !== undefined && withinDays !== null) {
    params.set("within_days", String(withinDays));
  }
  const query = params.toString() ? `?${params.toString()}` : "";
  return apiRequest(`/compliance/deadlines${query}`);
}

// Runs the daily sweep on demand. Idempotent server-side (obligations
// dedupe on project+rule+period, alerts on their dedupe key, and a
// Postgres advisory lock stops two callers overlapping), so a PM who
// clicks it twice loses nothing.
export function runComplianceTick() {
  return apiRequest("/compliance/tick", { method: "POST" });
}

export function getComplianceRuns(limit = 20) {
  return apiRequest(`/compliance/runs?limit=${limit}`);
}
