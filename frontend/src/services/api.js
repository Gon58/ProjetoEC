const API_URL = import.meta.env.VITE_API_URL

export async function healthCheck() {
  const res = await fetch(`${API_URL}/health`)
  return res.json()
}
