import { apiRequest, BASE_URL } from "./client";

export function createDailyLog(data) {
  return apiRequest("/daily-logs/", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function getDailyLog(dailyLogId) {
  return apiRequest(`/daily-logs/${dailyLogId}`);
}

export function getEventDailyLogs(eventId) {
  return apiRequest(`/daily-logs/event/${eventId}`);
}

// The full Daily Log list for a project - used by the "Daily Log" tab on
// the project overview page.
export function getProjectDailyLogs(projectId) {
  return apiRequest(`/daily-logs/project/${projectId}`);
}

export function updateDailyLog(dailyLogId, data) {
  return apiRequest(`/daily-logs/${dailyLogId}`, {
    method: "PUT",
    body: JSON.stringify(data),
  });
}

export function deleteDailyLog(dailyLogId) {
  return apiRequest(`/daily-logs/${dailyLogId}`, {
    method: "DELETE",
  });
}

export function getDailyLogReport(dailyLogId) {
  return apiRequest(`/daily-logs/${dailyLogId}/report`);
}

export function dailyLogReportPdfUrl(dailyLogId) {
  return `${BASE_URL}/daily-logs/${dailyLogId}/report/pdf`;
}

export function dailyLogReportExcelUrl(dailyLogId) {
  return `${BASE_URL}/daily-logs/${dailyLogId}/report/excel`;
}

// The Report tab's compiled Daily Log export - every Daily Log for the
// project, formatted like the reference site-log template, one day per
// section. startDate/endDate are optional (YYYY-MM-DD) - omitted, the
// full project history is included.
export function projectDailyLogReportPdfUrl(projectId, { startDate, endDate } = {}) {
  const params = new URLSearchParams();
  if (startDate) params.set("start_date", startDate);
  if (endDate) params.set("end_date", endDate);
  const query = params.toString();
  return `${BASE_URL}/daily-logs/project/${projectId}/report/pdf${query ? `?${query}` : ""}`;
}

export function projectDailyLogReportExcelUrl(projectId, { startDate, endDate } = {}) {
  const params = new URLSearchParams();
  if (startDate) params.set("start_date", startDate);
  if (endDate) params.set("end_date", endDate);
  const query = params.toString();
  return `${BASE_URL}/daily-logs/project/${projectId}/report/excel${query ? `?${query}` : ""}`;
}
