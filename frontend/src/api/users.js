import { apiRequest } from "./client";

export function registerUser(data) {
  return apiRequest("/users/", {
    method: "POST",
    body: JSON.stringify(data),
  });
}