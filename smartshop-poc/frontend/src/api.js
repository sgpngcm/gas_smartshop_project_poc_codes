import axios from "axios";

export const API_BASE = "http://localhost:8000";

export const api = axios.create({
  baseURL: `${API_BASE}/api`,
  withCredentials: true, // IMPORTANT for Django session cookie
});

// Attach JWT token to every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access");

  // Ensure headers object exists
  config.headers = config.headers || {};

  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  } else {
    // Optional: remove header if no token
    delete config.headers.Authorization;
  }

  return config;
});
