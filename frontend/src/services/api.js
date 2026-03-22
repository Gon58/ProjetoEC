import axios from "axios";

const API_BASE_URL = "http://localhost:8080";

const api = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,
});

export async function healthCheck() {
  const response = await api.get("/health");
  return response.data;
}

export async function getCurrentUser() {
  const response = await api.get("/auth/me");
  return response.data;
}

export async function getSteamProfile() {
  const response = await api.get("/auth/steam/profile");
  return response.data;
}

export async function getSteamInventory() {
  const response = await api.get("/auth/steam/inventory");
  return response.data;
}

export async function logoutSteam() {
  const response = await api.post("/auth/logout");
  return response.data;
}

export function getSteamLoginUrl() {
  return `${API_BASE_URL}/auth/steam/login`;
}

export default api;