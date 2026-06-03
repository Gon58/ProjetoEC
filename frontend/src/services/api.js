import axios from "axios";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8080";

const api = axios.create({
  baseURL: API_URL,
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
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data?.answer || "Erro ao comunicar com o agente");
  return data;
}

export async function getPriceHistory(limit = 5, days = 30) {
  const response = await api.get("/skins/price-history", { params: { limit, days } });
  return response.data;
}

export async function getSkinHistory(skinId, days = 30) {
  const response = await api.get(`/skins/${skinId}/history`, { params: { days } });
  return response.data;
}

export async function getInventoryPriceChanges(names, days = 14) {
  const response = await api.post("/skins/price-changes", { names, days });
  return response.data;
}

export async function searchSkins(q, limit = 10) {
  const response = await api.get("/skins/search", { params: { q, limit } });
  return response.data;
}

export async function getHistoryCount() {
  const response = await api.get("/skins/history-count");
  return response.data.count;
}

export async function getSteamMarketSkins() {
  const response = await api.get("/skins/steam-market");
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

export async function getLogs({ parentId = null, page = 1, pageSize = 5 } = {}) {
  const params = {
    page,
    page_size: pageSize,
  };

  if (parentId !== null && parentId !== undefined) {
    params.parent_id = parentId;
  }

  const response = await api.get("/logs", { params });
  return response.data;
}

export function getSteamLoginUrl() {
  return `${API_URL}/auth/steam/login`;
}

export default api;
