// Falls back to the FastAPI dev server default so the app works out of the
// box even before a .env is set up (see .env.example).
export const BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
const TOKEN_KEY = "ceip_token";

export function setToken(token) {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
}

export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

// FastAPI's validation errors (422) come back as
// { detail: [{ loc, msg, type }, ...] }, not a plain string - passing that
// straight into `new Error(...)` used to render as "[object Object]" in
// every snackbar/alert in the app, making a validation failure look like
// the feature itself was broken rather than telling the user what to fix.
function formatErrorDetail(errorBody) {
  const detail = errorBody?.detail;

  if (!detail) return null;
  if (typeof detail === "string") return detail;

  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        if (typeof item === "string") return item;
        const field = Array.isArray(item?.loc) ? item.loc.at(-1) : null;
        return field ? `${field}: ${item.msg}` : item?.msg;
      })
      .filter(Boolean)
      .join("; ");
  }

  return JSON.stringify(detail);
}

export async function apiRequest(path, options = {}) {
  const isFormData = options.body instanceof FormData;
  const token = getToken();

  const headers = {
    ...(isFormData ? {} : { "Content-Type": "application/json" }),
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...options.headers,
  };

  const response = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const errorBody = await response.json().catch(() => null);
    throw new Error(formatErrorDetail(errorBody) || `Request failed: ${response.status}`);
  }

  if (response.status === 204) return null;

  return response.json();
}