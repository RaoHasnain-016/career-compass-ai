import { auth } from "../firebase/firebase";

const DEFAULT_API_BASE_URL = import.meta.env.DEV
  ? "/api"
  : "";

export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || DEFAULT_API_BASE_URL;

const FALLBACK_API_BASE_URLS = import.meta.env.DEV
  ? [API_BASE_URL, "/api", "http://127.0.0.1:8000", "http://localhost:8000"]
  : [API_BASE_URL];

function uniqueUrls(urls) {
  // An empty base URL is intentional in production: it means same-origin.
  return [...new Set(urls.filter((url) => url !== undefined && url !== null))];
}

function buildUrl(baseUrl, path) {
  if (/^https?:\/\//i.test(path)) {
    return path;
  }

  return `${baseUrl}${path.startsWith("/") ? path : `/${path}`}`;
}

function isProxyBaseUrl(baseUrl) {
  return baseUrl === "/api" || baseUrl.endsWith("/api");
}

function shouldTryNextBaseUrl(error, baseUrl) {
  if (!error.status) return true;

  const retryableProxyStatuses = [500, 502, 503, 504];
  return (
    isProxyBaseUrl(baseUrl) &&
    retryableProxyStatuses.includes(error.status) &&
    typeof error.data === "string"
  );
}

function readErrorMessage(data, fallback) {
  if (!data) return fallback;

  if (typeof data === "string") {
    return data || fallback;
  }

  if (typeof data.detail === "string") {
    return data.detail;
  }

  if (typeof data.message === "string") {
    return data.message;
  }

  if (Array.isArray(data.detail)) {
    return data.detail
      .map((item) => item?.msg || item?.message || String(item))
      .join(", ");
  }

  return fallback;
}

export function getFirebaseUser() {
  return auth.currentUser;
}

export async function getFirebaseIdToken(forceRefresh = false) {
  const user = getFirebaseUser();

  if (!user) {
    const error = new Error("You must be logged in to continue.");
    error.status = 401;
    throw error;
  }

  return user.getIdToken(forceRefresh);
}

async function buildRequestConfig(options = {}) {
  const {
    method = "GET",
    body,
    headers = {},
    auth: useAuth = true,
    forceRefreshToken = false,
    ...rest
  } = options;

  const requestHeaders = { ...headers };

  if (useAuth) {
    const token = await getFirebaseIdToken(forceRefreshToken);
    requestHeaders.Authorization = `Bearer ${token}`;
  }

  let requestBody = body;

  if (
    body !== undefined &&
    body !== null &&
    !(body instanceof FormData) &&
    typeof body !== "string"
  ) {
    requestBody = JSON.stringify(body);
    requestHeaders["Content-Type"] =
      requestHeaders["Content-Type"] || "application/json";
  }

  if (typeof body === "string") {
    requestHeaders["Content-Type"] =
      requestHeaders["Content-Type"] || "application/json";
  }

  return {
    method,
    body: requestBody,
    headers: requestHeaders,
    ...rest,
  };
}

async function parseResponse(response) {
  const text = await response.text();

  let data = null;

  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      data = text;
    }
  }

  if (!response.ok) {
    const message = readErrorMessage(
      data,
      `Request failed with status ${response.status}`
    );

    const error = new Error(message);
    error.status = response.status;
    error.data = data;
    throw error;
  }

  return data;
}

export async function request(path, options = {}) {
  const config = await buildRequestConfig(options);
  const baseUrls = uniqueUrls(FALLBACK_API_BASE_URLS);

  let lastNetworkError = null;

  for (const baseUrl of baseUrls) {
    try {
      const url = buildUrl(baseUrl, path);

      console.log("API Request:", config.method, url);

      const response = await fetch(url, config);

      return await parseResponse(response);
    } catch (error) {
      if (!shouldTryNextBaseUrl(error, baseUrl)) {
        throw error;
      }

      console.error(`API network/CORS error for ${baseUrl}:`, error);
      lastNetworkError = error;
    }
  }

  const networkError = new Error(
    "Cannot connect to the backend API. Make sure the Career Compass server is running and try again."
  );

  networkError.cause = lastNetworkError;
  throw networkError;
}

export const get = (path, options = {}) =>
  request(path, {
    ...options,
    method: "GET",
  });

export const post = (path, body = undefined, options = {}) =>
  request(path, {
    ...options,
    method: "POST",
    body,
  });

export const put = (path, body = {}, options = {}) =>
  request(path, {
    ...options,
    method: "PUT",
    body,
  });

export const del = (path, options = {}) =>
  request(path, {
    ...options,
    method: "DELETE",
  });

export const api = {
  request,
  get,
  post,
  put,
  delete: del,
};

export default api;
