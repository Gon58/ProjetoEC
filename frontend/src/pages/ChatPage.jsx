import { useState } from "react";
import { chatWithAgent } from "../services/api";

const initialMessages = [
  { id: 1, author: "assistant", text: "Olá! Pergunta o que quiser sobre skins e preços." },
];

export default function ChatPage() {
  const [messages, setMessages] = useState(initialMessages);
  const [input, setInput] = useState("");
  const [isSending, setIsSending] = useState(false);

  async function handleSend() {
    const question = input.trim();
    if (!question || isSending) return;

    const userMessage = { id: Date.now(), author: "user", text: question };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsSending(true);

    try {
      const response = await chatWithAgent(question);
      setMessages((prev) => [
        ...prev,
        { id: Date.now() + 1, author: "assistant", text: response.answer },
      ]);
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now() + 1,
          author: "assistant",
          text: error.message || "Não foi possível obter resposta do agente.",
        },
      ]);
    } finally {
      setIsSending(false);
    }
  }

  return (
    <section className="chat-page">
      <div className="page-header">
        <div>
          <h2>Chatbot</h2>
          <p>Converse com o assistente para obter recomendações rápidas.</p>
        </div>
      </div>

      <div className="chat-shell">
        <div className="chat-messages">
          {messages.map((message) => (
            <div key={message.id} className={`message ${message.author}`}>
              <div className="message-author">{message.author === "user" ? "Tu" : "Assistente"}</div>
              <div className="message-text">{message.text}</div>
            </div>
          ))}
        </div>

        <div className="chat-input-row">
          <input
            type="text"
            value={input}
            onChange={(event) => setInput(event.target.value)}
            placeholder="Escreve a tua pergunta..."
            disabled={isSending}
            onKeyDown={(event) => {
              if (event.key === "Enter") handleSend();
            }}
          />
          <button className="primary-btn" onClick={handleSend} disabled={isSending}>
            {isSending ? "A enviar..." : "Enviar"}
          </button>
        </div>
      </div>
    </section>
  );
}
