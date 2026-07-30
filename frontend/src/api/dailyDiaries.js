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