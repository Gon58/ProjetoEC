const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8080"

export async function healthCheck() {
  const res = await fetch(`${API_URL}/health`)
  return res.json()
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
