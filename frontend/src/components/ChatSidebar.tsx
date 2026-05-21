"use client";

import { useState, useRef, useEffect } from "react";
import * as api from "@/lib/api";
import type { ChatMessage } from "@/lib/api";

type ChatSidebarProps = {
  userId: number;
  onBoardUpdated: () => void;
  isOpen: boolean;
  onClose: () => void;
};

export const ChatSidebar = ({ userId, onBoardUpdated, isOpen, onClose }: ChatSidebarProps) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const text = input.trim();
    if (!text || loading) return;

    const userMsg: ChatMessage = { role: "user", content: text };
    const updatedMessages = [...messages, userMsg];
    setMessages(updatedMessages);
    setInput("");
    setLoading(true);

    try {
      const response = await api.chatWithAI(userId, updatedMessages);
      const assistantMsg: ChatMessage = { role: "assistant", content: response.reply };
      setMessages([...updatedMessages, assistantMsg]);
      if (response.actions_applied.length > 0) {
        onBoardUpdated();
      }
    } catch {
      const errorMsg: ChatMessage = { role: "assistant", content: "Sorry, something went wrong." };
      setMessages([...updatedMessages, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <aside className="fixed right-0 top-0 z-50 flex h-full w-[360px] flex-col border-l border-[var(--stroke)] bg-white shadow-[-4px_0_24px_rgba(3,33,71,0.08)]">
      <div className="flex items-center justify-between border-b border-[var(--stroke)] px-5 py-4">
        <h2 className="text-sm font-semibold uppercase tracking-[0.2em] text-[var(--navy-dark)]">
          AI Assistant
        </h2>
        <button
          type="button"
          onClick={onClose}
          className="rounded-full p-1 text-[var(--gray-text)] transition hover:text-[var(--navy-dark)]"
          aria-label="Close chat"
        >
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
            <path d="M6 6l8 8M14 6l-8 8" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
          </svg>
        </button>
      </div>

      <div className="flex-1 overflow-y-auto px-5 py-4" data-testid="chat-messages">
        {messages.length === 0 && (
          <p className="text-center text-xs text-[var(--gray-text)]">
            Ask me to create, move, or update cards on your board.
          </p>
        )}
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`mb-3 rounded-xl px-4 py-3 text-sm leading-relaxed ${
              msg.role === "user"
                ? "ml-8 bg-[var(--primary-blue)] text-white"
                : "mr-8 bg-[var(--surface)] text-[var(--navy-dark)]"
            }`}
          >
            {msg.content}
          </div>
        ))}
        {loading && (
          <div className="mr-8 mb-3 rounded-xl bg-[var(--surface)] px-4 py-3 text-sm text-[var(--gray-text)]">
            Thinking...
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <form onSubmit={handleSubmit} className="border-t border-[var(--stroke)] px-5 py-4">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask the AI..."
            disabled={loading}
            className="flex-1 rounded-full border border-[var(--stroke)] bg-[var(--surface)] px-4 py-2 text-sm text-[var(--navy-dark)] outline-none placeholder:text-[var(--gray-text)] focus:border-[var(--primary-blue)]"
            data-testid="chat-input"
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="rounded-full bg-[var(--secondary-purple)] px-4 py-2 text-xs font-semibold uppercase tracking-wide text-white transition hover:opacity-90 disabled:opacity-50"
            data-testid="chat-send"
          >
            Send
          </button>
        </div>
      </form>
    </aside>
  );
};
