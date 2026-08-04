import { apiRequest, BASE_URL } from "./client";

export function getProjectReport(projectId) {
  return apiRequest(`/dashboard/${projectId}/report`);
}

export function reportExportUrl(projectId) {
  return `${BASE_URL}/dashboard/${projectId}/report/export`;
}

export function reportPdfUrl(projectId) {
  return `${BASE_URL}/dashboard/${projectId}/report/pdf`;
}

export function reportExcelUrl(projectId) {
  return `${BASE_URL}/dashboard/${projectId}/report/excel`;
}
