import { useState } from "react";

const initialMessages = [
  { id: 1, author: "assistant", text: "Olá! Pergunta o que quiser sobre skins e preços." },
];

const botResponses = {
  "dragon lore": "Dragon Lore é uma skin AWP Covert de alto valor e muito procurada.",
  "avg price": "A média de preço no recente dataset está em torno de €~500 para os itens listados.",
  default: "Estou aqui para ajudar com perguntas de skins; tenta algo como 'Qual skin é mais rara?'",
};

export default function ChatPage() {
  const [messages, setMessages] = useState(initialMessages);
  const [input, setInput] = useState("");

  function handleSend() {
    if (!input.trim()) return;

    const userMessage = { id: Date.now(), author: "user", text: input.trim() };
    const key = input.toLowerCase();
    const matched = Object.keys(botResponses).find((k) => key.includes(k));
    const botText = matched ? botResponses[matched] : botResponses.default;

    setMessages((prev) => [...prev, userMessage, { id: Date.now() + 1, author: "assistant", text: botText }]);
    setInput("");
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
            onKeyDown={(event) => {
              if (event.key === "Enter") handleSend();
            }}
          />
          <button className="primary-btn" onClick={handleSend}>Enviar</button>
        </div>
      </div>
    </section>
  );
}
