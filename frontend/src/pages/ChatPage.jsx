import { useState, useEffect, useRef } from "react";
import { chatWithAgent } from "../services/api";

const initialMessages = [
  { id: 1, author: "assistant", text: "Olá! Pergunta o que quiser sobre skins e preços." },
];

export default function ChatPage() {
  const [messages, setMessages] = useState(initialMessages);
  const [input, setInput] = useState("");
  const [isSending, setIsSending] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function handleSend() {
    const question = input.trim();
    if (!question || isSending) return;

    const userMessage = { id: Date.now(), author: "user", text: question };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsSending(true);

    try {
      const history = messages
        .filter((m) => m.id !== 1)   // exclude the static greeting
        .slice(-10)                   // keep only the last 10 messages (5 turns)
        .map((m) => ({
          role: m.author === "user" ? "user" : "assistant",
          content: m.text,
        }));
      const response = await chatWithAgent(question, history);
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now() + 1,
          author: "assistant",
          text: response.answer,
          dataTimestamp: response.data_timestamp || null,
        },
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
    <section className="flex flex-col gap-20 pb-20 pt-8 md:gap-24 md:pb-28 md:pt-12">
      <section className="px-8 md:px-16 lg:px-24">
        <div className="mb-6 flex justify-center">
          <img
            src="/TeacherBotConnor.png"
            alt="Teacher Bot Connor"
            className="h-40 w-40 border border-sky-300/35 object-cover shadow-[0_0_30px_rgba(56,189,248,0.22)] md:h-48 md:w-48"
          />
        </div>
        <h2 className="mb-10 text-center text-3xl font-extrabold uppercase tracking-[0.08em] text-transparent bg-white bg-clip-text md:text-4xl">
          Teacher Bot Connor
        </h2>
        <p className="mx-auto max-w-3xl text-center text-sm text-slate-400 md:text-base">
          Talk with Teacher Bot Connor! Ask anything about CS skins, market trends, or get personalized recommendations.
        </p>
      </section>

      <section className="px-8 md:px-16 lg:px-24">
          <div className="flex min-h-160 flex-col border border-slate-800/90 bg-[#17191A] p-5 md:p-6">
            <div className="max-h-130 flex-1 space-y-3 overflow-y-auto pr-1">
            {messages.map((message) => {
              const isUser = message.author === "user";
              return (
                <div key={message.id} className={`flex items-start gap-3 ${isUser ? "justify-end" : "justify-start"}`}>
                  {!isUser && (
                    <img
                      src="/TeacherBotConnor.png"
                      alt="Teacher Bot Connor"
                      className="h-9 w-9 shrink-0 border border-sky-300/30 object-cover"
                    />
                  )}

                  <div
                    className={`w-fit max-w-[86%] border px-3 py-2 ${
                      isUser
                        ? "ml-auto border-sky-500 bg-sky-600 text-white"
                        : "border-[#8c6d47] text-[#41321E]"
                    }`}
                    style={
                      isUser
                        ? undefined
                        : {
                            backgroundImage:
                              "linear-gradient(rgba(246, 234, 210, 0.9), rgba(246, 234, 210, 0.9)), url('/tsidelogo.webp')",
                            backgroundSize: "cover",
                            backgroundPosition: "center",
                          }
                    }
                  >
                    <div className={`mb-1 text-[0.72rem] ${isUser ? "text-sky-100" : "text-[#41321E]/80"}`}>
                      {isUser ? "Me" : "Teacher Bot Connor"}
                    </div>
                    <div className="leading-relaxed">{message.text}</div>
                    {!isUser && message.dataTimestamp && (
                      <div className="mt-2 border-t border-[#8c6d47]/30 pt-1 text-[0.65rem] text-[#41321E]/60">
                        Dados de: {message.dataTimestamp}
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
            <div ref={bottomRef} />
          </div>

          <div className="mt-4 flex flex-col gap-3 sm:flex-row">
            <input
              type="text"
              value={input}
              onChange={(event) => setInput(event.target.value)}
              placeholder="Escreve a tua pergunta..."
              disabled={isSending}
              className="w-full border border-slate-700 bg-[#0f172a] px-4 py-3 text-slate-100 outline-none transition focus:border-sky-400"
              onKeyDown={(event) => {
                if (event.key === "Enter") handleSend();
              }}
            />

            <button
              type="button"
              className="cursor-pointer border border-sky-200/40 bg-sky-400 px-8 py-3 text-sm font-semibold uppercase tracking-[0.08em] text-slate-950 transition-all hover:scale-[1.02] hover:bg-sky-300 disabled:cursor-not-allowed disabled:opacity-50"
              onClick={handleSend}
              disabled={isSending}
            >
              {isSending ? "A enviar..." : "Enviar"}
            </button>
          </div>
        </div>
      </section>
    </section>
  );
}
