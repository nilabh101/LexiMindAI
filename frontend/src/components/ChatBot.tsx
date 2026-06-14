/**
 * ChatBot — floating AI assistant powered by Gemini (falls back to rule-based).
 * Shows as a floating button; expands into a chat panel.
 */
import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { MessageSquare, X, Send, Bot, User, Loader2, ChevronDown } from "lucide-react";
import { sendChatMessage, ChatMessage } from "../lib/api";
import { useQuery } from "@tanstack/react-query";
import { listDocuments } from "../lib/api";

export function ChatBot() {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: "assistant",
      content: "Hi! I'm LexiMind AI. Upload a document and ask me anything about it — summaries, topics, explanations, or just general questions.",
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [docId, setDocId] = useState<number | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const { data: docsData } = useQuery({
    queryKey: ["documents"],
    queryFn: () => listDocuments().then((r) => r.data),
    enabled: open,
  });
  const docs: any[] = docsData || [];

  useEffect(() => {
    if (open) {
      setTimeout(() => inputRef.current?.focus(), 200);
    }
  }, [open]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const send = async () => {
    const text = input.trim();
    if (!text || loading) return;

    const userMsg: ChatMessage = { role: "user", content: text };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const res = await sendChatMessage(text, docId, messages.slice(-6));
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: res.data.reply },
      ]);
    } catch (e: any) {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: `Sorry, something went wrong: ${e.message}` },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleKey = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  };

  return (
    <>
      {/* Floating button */}
      <motion.button
        onClick={() => setOpen((v) => !v)}
        whileHover={{ scale: 1.08 }}
        whileTap={{ scale: 0.95 }}
        className="fixed bottom-6 right-6 z-50 w-14 h-14 rounded-full bg-gradient-to-br from-brand-500 to-purple-600 text-white shadow-2xl shadow-brand-500/40 flex items-center justify-center"
        aria-label="Open AI Chat"
      >
        <AnimatePresence mode="wait">
          {open ? (
            <motion.div key="close" initial={{ rotate: -90, opacity: 0 }} animate={{ rotate: 0, opacity: 1 }} exit={{ rotate: 90, opacity: 0 }}>
              <X size={22} />
            </motion.div>
          ) : (
            <motion.div key="open" initial={{ rotate: 90, opacity: 0 }} animate={{ rotate: 0, opacity: 1 }} exit={{ rotate: -90, opacity: 0 }}>
              <MessageSquare size={22} />
            </motion.div>
          )}
        </AnimatePresence>
      </motion.button>

      {/* Chat panel */}
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.95 }}
            transition={{ type: "spring", stiffness: 300, damping: 30 }}
            className="fixed bottom-24 right-6 z-50 w-[380px] max-w-[calc(100vw-2rem)] flex flex-col glass-card shadow-2xl overflow-hidden"
            style={{ height: "520px" }}
          >
            {/* Header */}
            <div className="flex items-center gap-3 p-4 border-b border-white/10 bg-gradient-to-r from-brand-600/20 to-purple-600/20 shrink-0">
              <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-brand-500 to-purple-500 flex items-center justify-center">
                <Bot size={16} className="text-white" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="font-semibold text-white text-sm">LexiMind AI</div>
                <div className="text-[10px] text-brand-400">Powered by Gemini</div>
              </div>
              {/* Document selector */}
              {docs.length > 0 && (
                <select
                  value={docId ?? ""}
                  onChange={(e) => setDocId(e.target.value ? Number(e.target.value) : null)}
                  className="text-xs bg-white/10 border border-white/10 rounded-lg px-2 py-1 text-slate-300 max-w-[120px] truncate"
                >
                  <option value="">No doc</option>
                  {docs.map((d: any) => (
                    <option key={d.id} value={d.id}>
                      {(d.original_filename || d.filename || "").slice(0, 18)}
                    </option>
                  ))}
                </select>
              )}
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-3">
              {messages.map((msg, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  className={`flex gap-2.5 ${msg.role === "user" ? "flex-row-reverse" : ""}`}
                >
                  <div className={`w-7 h-7 rounded-full flex items-center justify-center shrink-0 mt-0.5 ${
                    msg.role === "user"
                      ? "bg-brand-600/30 text-brand-300"
                      : "bg-purple-600/30 text-purple-300"
                  }`}>
                    {msg.role === "user" ? <User size={13} /> : <Bot size={13} />}
                  </div>
                  <div className={`max-w-[80%] px-3.5 py-2.5 rounded-2xl text-sm leading-relaxed whitespace-pre-wrap ${
                    msg.role === "user"
                      ? "bg-brand-600/25 text-white rounded-tr-sm"
                      : "bg-white/8 text-slate-200 rounded-tl-sm"
                  }`}>
                    {msg.content}
                  </div>
                </motion.div>
              ))}

              {loading && (
                <div className="flex gap-2.5">
                  <div className="w-7 h-7 rounded-full bg-purple-600/30 text-purple-300 flex items-center justify-center shrink-0">
                    <Bot size={13} />
                  </div>
                  <div className="px-3.5 py-2.5 rounded-2xl rounded-tl-sm bg-white/8 flex items-center gap-2">
                    <Loader2 size={13} className="text-brand-400 animate-spin" />
                    <span className="text-xs text-slate-400">Thinking…</span>
                  </div>
                </div>
              )}
              <div ref={bottomRef} />
            </div>

            {/* Quick prompts */}
            {messages.length === 1 && (
              <div className="px-4 pb-2 flex flex-wrap gap-1.5 shrink-0">
                {[
                  "Summarize the document",
                  "What are the main topics?",
                  "What's the reading level?",
                ].map((prompt) => (
                  <button
                    key={prompt}
                    onClick={() => { setInput(prompt); inputRef.current?.focus(); }}
                    className="text-xs px-3 py-1.5 rounded-full bg-white/8 text-slate-300 hover:bg-white/15 transition-colors border border-white/10"
                  >
                    {prompt}
                  </button>
                ))}
              </div>
            )}

            {/* Input */}
            <div className="p-3 border-t border-white/10 shrink-0">
              <div className="flex gap-2 items-center bg-white/8 rounded-xl px-3 py-2 border border-white/10 focus-within:border-brand-500/50 transition-colors">
                <input
                  ref={inputRef}
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKey}
                  placeholder={docId ? "Ask about the document…" : "Ask me anything…"}
                  className="flex-1 bg-transparent text-sm text-white placeholder-slate-500 outline-none"
                />
                <button
                  onClick={send}
                  disabled={!input.trim() || loading}
                  className="w-7 h-7 rounded-lg bg-brand-600 hover:bg-brand-500 text-white flex items-center justify-center transition-all disabled:opacity-30 disabled:cursor-not-allowed shrink-0"
                >
                  <Send size={13} />
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
