import { apiRequest, setToken, clearToken, getToken } from "./client";

export function login(email, password) {
  const body = new URLSearchParams();
  body.append("username", email);
  body.append("password", password);

  return apiRequest("/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body,
  }).then((data) => {
    setToken(data.access_token);
    return data;
  });
}

export function logout() {
  clearToken();
}

export function isLoggedIn() {
  return Boolean(getToken());
}