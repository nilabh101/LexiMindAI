import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { MessageCircle, Send, Bot, User, Loader2, Zap } from "lucide-react";
import { sendChatMessage } from "../../lib/api";
import type { ChatMessage } from "../../lib/api";
import { loadUser } from "../../store/userStore";
import { DEMO_USER } from "../../data/demoData";
import { SUBJECTS } from "../../data/curriculum";

const QUICK_ACTIONS = [
  { label: "Explain this concept", prompt: "Explain Euler's theorem in simple terms." },
  { label: "Give me an example", prompt: "Give me a worked example of applying Euler's theorem." },
  { label: "Simplify it", prompt: "Explain partial derivatives more simply, like I'm a beginner." },
  { label: "Test me", prompt: "Give me a quick question to test my understanding of partial derivatives." },
];

export function TutorPage() {
  const user = loadUser() ?? DEMO_USER;
  const subjects = SUBJECTS.filter(s => user.academicProfile?.subjectIds.includes(s.id));

  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: "assistant",
      content: `Hi ${user.name.split(" ")[0]}! I'm your LexiMind AI Tutor. I'm aware of your curriculum — you're currently studying ${subjects[0]?.name ?? "your subjects"}.\n\nAsk me to explain a concept, give you examples, simplify a topic, or test your understanding!`,
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [docId, setDocId] = useState<number | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const send = async (text?: string) => {
    const msg = (text ?? input).trim();
    if (!msg || loading) return;
    setInput("");
    setMessages(p => [...p, { role: "user", content: msg }]);
    setLoading(true);
    try {
      const res = await sendChatMessage(msg, docId, messages.slice(-6));
      setMessages(p => [...p, { role: "assistant", content: res.data.reply }]);
    } catch {
      setMessages(p => [...p, { role: "assistant", content: "Sorry, I couldn't reach the AI service. Please try again." }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-64px)] lg:h-screen p-4 lg:p-6 max-w-3xl mx-auto">
      {/* Header */}
      <div className="flex items-center gap-3 mb-4 shrink-0">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-purple-500 to-indigo-600 flex items-center justify-center">
          <Bot size={18} className="text-white" />
        </div>
        <div>
          <h1 className="text-lg font-bold text-white">AI Tutor</h1>
          <p className="text-xs text-slate-400">Context-aware · knows your curriculum</p>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto space-y-4 pr-1 mb-4">
        {messages.map((msg, i) => (
          <motion.div key={i} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}
            className={`flex gap-3 ${msg.role === "user" ? "flex-row-reverse" : ""}`}>
            <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 mt-0.5 ${msg.role === "user" ? "bg-indigo-600/30 text-indigo-300" : "bg-purple-600/30 text-purple-300"}`}>
              {msg.role === "user" ? <User size={14} /> : <Bot size={14} />}
            </div>
            <div className={`max-w-[80%] px-4 py-3 rounded-2xl text-sm leading-relaxed whitespace-pre-wrap ${msg.role === "user" ? "bg-indigo-600/25 text-white rounded-tr-sm" : "bg-white/6 text-slate-200 rounded-tl-sm"}`}>
              {msg.content}
            </div>
          </motion.div>
        ))}
        {loading && (
          <div className="flex gap-3">
            <div className="w-8 h-8 rounded-full bg-purple-600/30 text-purple-300 flex items-center justify-center"><Bot size={14} /></div>
            <div className="px-4 py-3 rounded-2xl bg-white/6 flex items-center gap-2">
              <Loader2 size={13} className="text-indigo-400 animate-spin" />
              <span className="text-xs text-slate-400">Thinking…</span>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Quick actions */}
      {messages.length <= 2 && (
        <div className="flex flex-wrap gap-2 mb-3 shrink-0">
          {QUICK_ACTIONS.map(a => (
            <button key={a.label} onClick={() => send(a.prompt)}
              className="text-xs px-3 py-1.5 rounded-full bg-white/5 border border-white/8 text-slate-300 hover:bg-white/10 hover:text-white transition-all flex items-center gap-1.5">
              <Zap size={10} className="text-indigo-400" /> {a.label}
            </button>
          ))}
        </div>
      )}

      {/* Input */}
      <div className="shrink-0 flex gap-2 items-center bg-white/5 border border-white/10 rounded-2xl px-4 py-2.5 focus-within:border-indigo-500/50 transition-colors">
        <input value={input} onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === "Enter" && !e.shiftKey && (e.preventDefault(), send())}
          placeholder="Ask anything about your subjects…"
          className="flex-1 bg-transparent text-sm text-white placeholder-slate-500 outline-none" />
        <button onClick={() => send()} disabled={!input.trim() || loading}
          className="w-8 h-8 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:opacity-30 text-white flex items-center justify-center transition-all shrink-0">
          <Send size={14} />
        </button>
      </div>
    </div>
  );
}
