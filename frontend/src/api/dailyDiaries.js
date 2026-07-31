import { apiRequest } from "./client";

export function createDailyDiary(data) {
  return apiRequest("/daily-diaries/", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function getDailyDiary(diaryId) {
  return apiRequest(`/daily-diaries/${diaryId}`);
}

export function getEventDiaries(eventId) {
  return apiRequest(`/daily-diaries/event/${eventId}`);
}

// The full Daily Diary list for a project - was never called from
// anywhere in the app, which is why a saved diary entry appeared to
// vanish: there was no screen that ever fetched this endpoint. Used by
// the "Daily Diary" tab on the project overview page.
export function getProjectDiaries(projectId) {
  return apiRequest(`/daily-diaries/project/${projectId}`);
}

export function updateDailyDiary(diaryId, data) {
  return apiRequest(`/daily-diaries/${diaryId}`, {
    method: "PUT",
    body: JSON.stringify(data),
  });
}

export function deleteDailyDiary(diaryId) {
  return apiRequest(`/daily-diaries/${diaryId}`, {
    method: "DELETE",
  });
}

export function getDailyReport(diaryId) {
  return apiRequest(`/daily-diaries/${diaryId}/report`);
}