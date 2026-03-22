const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8080"
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

export async function chatWithAgent(message) {
  const res = await fetch(`${API_URL}/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ message }),
  })

  const data = await res.json()

  if (!res.ok) {
    throw new Error(data?.answer || "Erro ao comunicar com o agente")
  }

  return data
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
