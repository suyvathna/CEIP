import { apiRequest } from "./client";

// Always scoped to one project - there is no cross-project search
// anywhere in this app.
export function searchIntelligence(query, projectId) {
  const params = new URLSearchParams({ q: query });
  if (projectId) params.set("project_id", projectId);
  return apiRequest(`/intelligence/search?${params.toString()}`);
}
