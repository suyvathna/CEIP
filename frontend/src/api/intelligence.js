import { apiRequest } from "./client";

export function searchIntelligence(query) {
  return apiRequest(`/intelligence/search?q=${encodeURIComponent(query)}`);
}
