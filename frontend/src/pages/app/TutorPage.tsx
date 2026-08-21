import { useState, useRef, useEffect } from "react";
import { motion } from "framer-motion";
import { Send, Bot, User, Loader2, Zap } from "lucide-react";
import { sendTutorMessage, getAiStatus } from "../../lib/api";
import type { ChatMessage } from "../../lib/api";
import { loadUser } from "../../store/userStore";
import { SUBJECTS } from "../../data/curriculum";
import {
  currentUserId, currentSubjectId, fetchWeakConcepts, masteryColor,
  type WeakConcept,
} from "../../services/adaptiveEngine";

/** Backend tutor actions — each one is answered from stored academic + performance data. */
const ACTIONS: { action: string; label: string; prompt: string }[] = [
  { action: "EXPLAIN",          label: "Explain",          prompt: "Explain this concept using my notes." },
  { action: "SIMPLIFY",         label: "Simplify",         prompt: "Explain it more simply, like I'm a beginner." },
  { action: "EXAMPLE",          label: "Example",          prompt: "Give me a worked example." },
  { action: "HINT",             label: "Hint",             prompt: "Give me a hint, not the full answer." },
  { action: "TEST_ME",          label: "Test me",          prompt: "Test me on this concept." },
  { action: "SIMILAR_QUESTION", label: "Similar question", prompt: "Give me a similar question to practise." },
  { action: "EXPLAIN_MISTAKE",  label: "Explain my mistake", prompt: "Explain the last question I got wrong." },
];

interface Msg extends ChatMessage {
  sources?: { title?: string; page?: number | null; year?: number | null; source?: string }[];
}

function formatSource(s: any): string {
  const bits: string[] = [];
  if (s.title) bits.push(s.title);
  if (s.year) bits.push(`${s.year} PYQ`);
  if (s.page != null) bits.push(`page ${s.page}`);
  if (!bits.length && s.source) bits.push(s.source);
  return bits.join(" · ");
}

export function TutorPage() {
  const user = loadUser();
  const userId = currentUserId(user);
  const subjectId = currentSubjectId(user);
  const subjects = SUBJECTS.filter(s => user?.academicProfile?.subjectIds?.includes(s.id));

  const [messages, setMessages] = useState<Msg[]>([
    {
      role: "assistant",
      content: `Hi ${user?.name?.split(" ")[0] ?? "there"}! I'm your LexiMind AI Tutor. I use your notes, your PYQs and your own quiz performance — I only comment on your progress when there is real data behind it.`,
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [docId] = useState<number | null>(null);
  const [weak, setWeak] = useState<WeakConcept[]>([]);
  const [focusConcept, setFocusConcept] = useState<string | undefined>(undefined);
  const [provider, setProvider] = useState<{ provider?: string; available?: boolean } | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages]);

  useEffect(() => {
    fetchWeakConcepts(userId, subjectId)
      .then(w => { setWeak(w); setFocusConcept(c => c ?? w[0]?.conceptId); })
      .catch(() => setWeak([]));
    getAiStatus().then(r => setProvider(r.data)).catch(() => setProvider(null));
  }, [userId, subjectId]);

  const send = async (text?: string, action?: string) => {
    const msg = (text ?? input).trim();
    if (!msg || loading) return;
    setInput("");
    setMessages(p => [...p, { role: "user", content: msg }]);
    setLoading(true);
    try {
      const res = await sendTutorMessage(msg, {
        docId,
        history: messages.slice(-6).map(m => ({ role: m.role, content: m.content })),
        userId,
        subjectId: subjects[0]?.id ?? subjectId,
        conceptId: focusConcept,
        educationLevel: user?.academicProfile?.educationLevel,
        course: user?.academicProfile?.courseId,
        action,
      });
      setMessages(p => [...p, {
        role: "assistant",
        content: res.data.reply,
        sources: res.data.sources ?? [],
      }]);
    } catch {
      setMessages(p => [...p, {
        role: "assistant",
        content: "Sorry, I couldn't reach the tutor service. Your notes, quizzes and progress still work offline.",
      }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-64px)] lg:h-screen p-4 lg:p-6 max-w-3xl mx-auto">
      {/* Header */}
      <div className="flex items-center gap-3 mb-3 shrink-0">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-purple-500 to-indigo-600 flex items-center justify-center">
          <Bot size={18} className="text-white" />
        </div>
        <div className="flex-1">
          <h1 className="text-lg font-bold text-white">AI Tutor</h1>
          <p className="text-xs text-slate-400">
            Grounded in your notes, PYQs and mastery
            {provider && !provider.available ? " · offline mode (retrieval only)" : ""}
          </p>
        </div>
      </div>

      {/* Focus concept — drives the context sent to the tutor */}
      {weak.length > 0 && (
        <div className="flex items-center gap-2 flex-wrap mb-3 shrink-0">
          <span className="text-xs text-slate-500">Focus:</span>
          {weak.slice(0, 4).map(w => (
            <button key={w.conceptId} onClick={() => setFocusConcept(w.conceptId)}
              className={`text-xs px-3 py-1.5 rounded-full border transition-all ${
                focusConcept === w.conceptId
                  ? "bg-indigo-600/25 border-indigo-500/40 text-white"
                  : "bg-white/4 border-white/8 text-slate-300 hover:bg-white/8"
              }`}>
              {w.concept} <span className={masteryColor(w.mastery)}>{w.mastery}%</span>
            </button>
          ))}
        </div>
      )}

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
              {!!msg.sources?.length && (
                <div className="mt-3 pt-2 border-t border-white/10">
                  <div className="text-[10px] uppercase tracking-wider text-slate-500 mb-1">Sources</div>
                  {msg.sources.slice(0, 4).map((s, j) => {
                    const label = formatSource(s);
                    return label ? <div key={j} className="text-xs text-slate-400">{label}</div> : null;
                  })}
                </div>
              )}
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

      {/* Tutor actions */}
      <div className="flex flex-wrap gap-2 mb-3 shrink-0">
        {ACTIONS.map(a => (
          <button key={a.action} onClick={() => send(a.prompt, a.action)} disabled={loading}
            className="text-xs px-3 py-1.5 rounded-full bg-white/5 border border-white/8 text-slate-300 hover:bg-white/10 hover:text-white disabled:opacity-40 transition-all flex items-center gap-1.5">
            <Zap size={10} className="text-indigo-400" /> {a.label}
          </button>
        ))}
      </div>

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
