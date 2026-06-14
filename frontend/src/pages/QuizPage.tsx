import { useState, useCallback } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { motion, AnimatePresence } from "framer-motion";
import {
  Zap, ChevronDown, ChevronUp, CheckCircle, XCircle, Trophy,
  RotateCcw, Eye, EyeOff, ChevronLeft, ChevronRight,
  Layers, ListChecks, BookOpen, FileText, Plus, X,
} from "lucide-react";
import { useSearchParams } from "react-router-dom";
import { getQuiz, getFlashcards, getQuestions, multiDocumentQuiz, listDocuments } from "../lib/api";
import { DocSelector } from "../components/DocSelector";
import { LoadingSpinner } from "../components/LoadingSpinner";
import { PageHeader } from "../components/PageHeader";
import confetti from "canvas-confetti";

// ─── types ────────────────────────────────────────────────────────────────────
interface MCQ {
  id?: number;
  question: string;
  options: string[];
  answer: string;
  difficulty: string;
  explanation: string;
  topic?: string;
  source_document?: string;
}
interface Flashcard { id: number; front: string; back: string; type: string; }
type Mode = "choose" | "quiz" | "study" | "flashcards" | "results";

// ─── difficulty badge ─────────────────────────────────────────────────────────
function DiffBadge({ level }: { level: string }) {
  const cls: Record<string, string> = {
    easy:        "bg-emerald-500/15 text-emerald-300 border-emerald-500/30",
    medium:      "bg-amber-500/15 text-amber-300 border-amber-500/30",
    hard:        "bg-red-500/15 text-red-300 border-red-500/30",
    application: "bg-sky-500/15 text-sky-300 border-sky-500/30",
    critical:    "bg-purple-500/15 text-purple-300 border-purple-500/30",
  };
  return (
    <span className={`text-[10px] px-2 py-0.5 rounded-full border font-medium shrink-0 ${cls[level] || cls.medium}`}>
      {level}
    </span>
  );
}

// ─── MCQ Quiz Component ────────────────────────────────────────────────────────
function MCQQuiz({ questions, onFinish }: { questions: MCQ[]; onFinish: (a: Record<number, string>) => void }) {
  const [current, setCurrent] = useState(0);
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [showExpl, setShowExpl] = useState(false);

  const q = questions[current];
  const answered = answers[current] !== undefined;
  const isCorrect = answered && answers[current] === q.answer;

  const pick = (opt: string) => {
    if (answered) return;
    setAnswers(p => ({ ...p, [current]: opt }));
    setShowExpl(true);
  };

  const next = () => {
    setShowExpl(false);
    if (current < questions.length - 1) setCurrent(c => c + 1);
    else onFinish(answers);
  };

  return (
    <div className="max-w-2xl mx-auto">
      {/* Progress */}
      <div className="flex items-center gap-3 mb-5">
        <div className="flex-1 bg-white/10 rounded-full h-2">
          <div className="bg-brand-500 h-2 rounded-full transition-all" style={{ width: `${((current + 1) / questions.length) * 100}%` }} />
        </div>
        <span className="text-sm text-slate-400 shrink-0">{current + 1} / {questions.length}</span>
      </div>

      <AnimatePresence mode="wait">
        <motion.div key={current} initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} className="glass-card p-6">
          <div className="flex items-start justify-between gap-3 mb-5">
            <div className="flex-1">
              {q.source_document && (
                <div className="flex items-center gap-1.5 text-[10px] text-slate-500 mb-2">
                  <FileText size={10} /> {q.source_document}
                </div>
              )}
              <p className="text-white font-medium text-base leading-relaxed">{q.question}</p>
            </div>
            <DiffBadge level={q.difficulty} />
          </div>

          <div className="space-y-2.5">
            {q.options.map((opt, i) => {
              let cls = "border-white/10 bg-white/5 hover:bg-white/10 text-slate-200 cursor-pointer";
              if (answered) {
                if (opt === q.answer) cls = "border-emerald-500/60 bg-emerald-500/15 text-emerald-200";
                else if (opt === answers[current]) cls = "border-red-500/60 bg-red-500/15 text-red-300";
                else cls = "border-white/5 bg-white/3 text-slate-500";
              }
              return (
                <button key={i} onClick={() => pick(opt)} disabled={answered}
                  className={`w-full text-left px-4 py-3 rounded-xl border transition-all text-sm flex items-center gap-3 ${cls}`}>
                  <span className="w-6 h-6 rounded-full border border-current flex items-center justify-center text-xs font-bold shrink-0">
                    {String.fromCharCode(65 + i)}
                  </span>
                  <span className="flex-1 leading-snug">{opt}</span>
                  {answered && opt === q.answer && <CheckCircle size={14} className="text-emerald-400 shrink-0" />}
                  {answered && opt === answers[current] && opt !== q.answer && <XCircle size={14} className="text-red-400 shrink-0" />}
                </button>
              );
            })}
          </div>

          <AnimatePresence>
            {showExpl && answered && (
              <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: "auto" }} exit={{ opacity: 0, height: 0 }}
                className={`mt-4 p-4 rounded-xl text-sm overflow-hidden ${isCorrect ? "bg-emerald-500/10 border border-emerald-500/30 text-emerald-200" : "bg-red-500/10 border border-red-500/30 text-red-200"}`}>
                <div className="font-semibold mb-1 flex items-center gap-2">
                  {isCorrect ? <><CheckCircle size={13} /> Correct!</> : <><XCircle size={13} /> Incorrect</>}
                </div>
                <p className="text-slate-300 text-xs leading-relaxed">{q.explanation}</p>
              </motion.div>
            )}
          </AnimatePresence>

          <div className="flex items-center justify-between mt-5">
            <button onClick={() => { setShowExpl(false); setCurrent(c => Math.max(0, c - 1)); }}
              disabled={current === 0} className="btn-ghost text-sm flex items-center gap-1 disabled:opacity-30">
              <ChevronLeft size={15} /> Back
            </button>
            <button onClick={next} disabled={!answered} className="btn-primary text-sm flex items-center gap-2 disabled:opacity-40">
              {current === questions.length - 1 ? <><Trophy size={14} /> Finish</> : <>Next <ChevronRight size={15} /></>}
            </button>
          </div>
        </motion.div>
      </AnimatePresence>
    </div>
  );
}

// ─── Results ──────────────────────────────────────────────────────────────────
function Results({ questions, answers, onRetry, onFlashcards }: {
  questions: MCQ[]; answers: Record<number, string>; onRetry: () => void; onFlashcards: () => void;
}) {
  const [expanded, setExpanded] = useState(false);
  const score = questions.filter((q, i) => answers[i] === q.answer).length;
  const pct = Math.round((score / questions.length) * 100);
  const color = pct >= 80 ? "text-emerald-400" : pct >= 60 ? "text-amber-400" : "text-red-400";

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="max-w-2xl mx-auto space-y-5">
      <div className="glass-card p-8 text-center">
        <div className={`text-7xl font-black ${color} mb-2`}>{pct}%</div>
        <div className="text-white text-xl font-semibold mb-1">
          {pct >= 90 ? "Excellent!" : pct >= 75 ? "Good job!" : pct >= 60 ? "Keep going!" : "Need more practice"}
        </div>
        <div className="text-slate-400">{score} / {questions.length} correct</div>
        <div className="flex rounded-xl overflow-hidden mt-5 h-3">
          <div className="bg-emerald-500 transition-all" style={{ width: `${pct}%` }} />
          <div className="bg-red-500/50 flex-1" />
        </div>
        <div className="flex gap-3 justify-center mt-5">
          <button onClick={onRetry} className="btn-ghost flex items-center gap-2 text-sm"><RotateCcw size={14} /> Retry</button>
          <button onClick={onFlashcards} className="btn-primary flex items-center gap-2 text-sm"><Layers size={14} /> Flashcards</button>
        </div>
      </div>

      <div className="glass-card overflow-hidden">
        <button onClick={() => setExpanded(v => !v)}
          className="w-full p-4 flex items-center justify-between text-sm font-medium text-slate-300 hover:text-white border-b border-white/10">
          <span className="flex items-center gap-2"><ListChecks size={14} className="text-brand-400" /> Review All Answers</span>
          {expanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
        </button>
        <AnimatePresence>
          {expanded && (
            <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: "auto", opacity: 1 }} exit={{ height: 0, opacity: 0 }}
              className="overflow-hidden divide-y divide-white/5">
              {questions.map((q, i) => {
                const correct = answers[i] === q.answer;
                return (
                  <div key={i} className="p-4">
                    <div className="flex items-start gap-3">
                      {correct ? <CheckCircle size={15} className="text-emerald-400 mt-0.5 shrink-0" /> : <XCircle size={15} className="text-red-400 mt-0.5 shrink-0" />}
                      <div className="flex-1">
                        <p className="text-sm text-white mb-2 font-medium">{q.question}</p>
                        <div className="text-xs space-y-1">
                          <div className="flex gap-2"><span className="text-slate-500">Your answer:</span><span className={correct ? "text-emerald-400" : "text-red-400"}>{answers[i] ?? "—"}</span></div>
                          {!correct && <div className="flex gap-2"><span className="text-slate-500">Correct:</span><span className="text-emerald-400">{q.answer}</span></div>}
                          <div className="mt-1.5 p-2 rounded-lg bg-white/5 text-slate-400 leading-relaxed">{q.explanation}</div>
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </motion.div>
  );
}

// ─── Flashcard Flip Mode ─────────────────────────────────────────────────────
function FlashcardMode({ cards }: { cards: Flashcard[] }) {
  const [idx, setIdx] = useState(0);
  const [flipped, setFlipped] = useState(false);
  const [known, setKnown] = useState<Set<number>>(new Set());

  const card = cards[idx];
  const allDone = known.size === cards.length;

  const mark = (ok: boolean) => {
    setFlipped(false);
    setTimeout(() => {
      if (ok) setKnown(s => new Set([...s, idx]));
      setIdx(i => Math.min(cards.length - 1, i + 1));
    }, 120);
  };

  if (allDone) return (
    <div className="max-w-md mx-auto glass-card p-10 text-center">
      <div className="text-5xl mb-4">🎉</div>
      <h3 className="text-2xl font-bold text-white mb-2">All done!</h3>
      <p className="text-slate-400 mb-5">You reviewed all {cards.length} cards.</p>
      <button onClick={() => { setIdx(0); setKnown(new Set()); setFlipped(false); }} className="btn-primary flex items-center gap-2 mx-auto"><RotateCcw size={14} /> Start Over</button>
    </div>
  );

  return (
    <div className="max-w-lg mx-auto">
      <div className="flex items-center justify-between text-sm text-slate-400 mb-4">
        <span className="flex items-center gap-1.5"><CheckCircle size={13} className="text-emerald-400" /> {known.size} known</span>
        <span>{idx + 1} / {cards.length}</span>
        <span className="flex items-center gap-1.5"><XCircle size={13} className="text-red-400" /> {cards.length - known.size - (known.has(idx) ? 0 : 0)} remaining</span>
      </div>
      <div className="bg-white/10 rounded-full h-1.5 mb-5">
        <div className="bg-emerald-500 h-1.5 rounded-full transition-all" style={{ width: `${(known.size / cards.length) * 100}%` }} />
      </div>

      <div className="h-52 cursor-pointer" style={{ perspective: "1200px" }} onClick={() => setFlipped(v => !v)}>
        <motion.div animate={{ rotateY: flipped ? 180 : 0 }} transition={{ type: "spring", stiffness: 300, damping: 30 }}
          style={{ transformStyle: "preserve-3d" }} className="relative w-full h-full">
          <div className="absolute inset-0 glass-card p-7 flex flex-col items-center justify-center text-center" style={{ backfaceVisibility: "hidden" }}>
            <span className="text-[10px] text-brand-400 mb-3 uppercase tracking-wider">{card.type === "definition" ? "Term" : "Question"}</span>
            <p className="text-lg font-semibold text-white leading-snug">{card.front}</p>
            <p className="text-xs text-slate-500 mt-4 flex items-center gap-1"><Eye size={10} /> Click to reveal</p>
          </div>
          <div className="absolute inset-0 glass-card p-7 flex flex-col items-center justify-center text-center bg-purple-900/20 border-purple-500/20" style={{ backfaceVisibility: "hidden", transform: "rotateY(180deg)" }}>
            <span className="text-[10px] text-purple-400 mb-3 uppercase tracking-wider">{card.type === "definition" ? "Definition" : "Answer"}</span>
            <p className="text-sm text-slate-200 leading-relaxed">{card.back}</p>
          </div>
        </motion.div>
      </div>

      <AnimatePresence>
        {flipped && (
          <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} className="flex gap-3 mt-4 justify-center">
            <button onClick={() => mark(false)} className="flex-1 py-3 rounded-xl border border-red-500/40 bg-red-500/10 text-red-300 hover:bg-red-500/20 text-sm flex items-center justify-center gap-2">
              <XCircle size={14} /> Still Learning
            </button>
            <button onClick={() => mark(true)} className="flex-1 py-3 rounded-xl border border-emerald-500/40 bg-emerald-500/10 text-emerald-300 hover:bg-emerald-500/20 text-sm flex items-center justify-center gap-2">
              <CheckCircle size={14} /> Got It
            </button>
          </motion.div>
        )}
      </AnimatePresence>

      <div className="flex justify-between mt-3">
        <button onClick={() => { setFlipped(false); setIdx(i => Math.max(0, i - 1)); }} disabled={idx === 0} className="btn-ghost text-sm flex items-center gap-1 disabled:opacity-30"><ChevronLeft size={14} /> Prev</button>
        <button onClick={() => { setFlipped(false); setIdx(i => Math.min(cards.length - 1, i + 1)); }} disabled={idx === cards.length - 1} className="btn-ghost text-sm flex items-center gap-1 disabled:opacity-30">Next <ChevronRight size={14} /></button>
      </div>
    </div>
  );
}

// ─── Practice (side-by-side) ──────────────────────────────────────────────────
function PracticeMode({ cards }: { cards: Flashcard[] }) {
  const [idx, setIdx] = useState(0);
  return (
    <div className="max-w-3xl mx-auto">
      <div className="flex items-center justify-between mb-4 text-sm text-slate-400">
        <span>{idx + 1} / {cards.length}</span>
        <div className="flex gap-2">
          <button onClick={() => setIdx(i => Math.max(0, i - 1))} disabled={idx === 0} className="btn-ghost px-3 py-1.5 text-xs disabled:opacity-30 flex items-center gap-1"><ChevronLeft size={13} /> Prev</button>
          <button onClick={() => setIdx(i => Math.min(cards.length - 1, i + 1))} disabled={idx === cards.length - 1} className="btn-ghost px-3 py-1.5 text-xs disabled:opacity-30 flex items-center gap-1">Next <ChevronRight size={13} /></button>
        </div>
      </div>
      <div className="grid grid-cols-2 gap-4">
        <div className="glass-card p-6 border-brand-500/20">
          <div className="text-xs text-brand-400 uppercase tracking-wider mb-3 flex items-center gap-1.5"><EyeOff size={11} /> Question / Term</div>
          <p className="text-white font-medium leading-relaxed">{cards[idx].front}</p>
        </div>
        <div className="glass-card p-6 border-purple-500/20 bg-purple-900/10">
          <div className="text-xs text-purple-400 uppercase tracking-wider mb-3 flex items-center gap-1.5"><Eye size={11} /> Answer / Definition</div>
          <p className="text-slate-200 leading-relaxed text-sm">{cards[idx].back}</p>
        </div>
      </div>
      <div className="flex gap-1.5 mt-4 flex-wrap">
        {cards.map((_, i) => (
          <button key={i} onClick={() => setIdx(i)}
            className={`w-7 h-7 rounded-lg text-xs font-medium transition-all ${i === idx ? "bg-brand-600 text-white" : "bg-white/5 text-slate-400 hover:bg-white/10"}`}>
            {i + 1}
          </button>
        ))}
      </div>
    </div>
  );
}

// ─── Study Questions ──────────────────────────────────────────────────────────
function StudyQuestions({ docId }: { docId: number }) {
  const [expandedQ, setExpandedQ] = useState<string | null>(null);
  const { data, isLoading } = useQuery({
    queryKey: ["questions", docId],
    queryFn: () => getQuestions(docId).then(r => r.data),
  });

  const diffColor: Record<string, string> = {
    easy: "bg-emerald-500/15 text-emerald-300",
    medium: "bg-amber-500/15 text-amber-300",
    hard: "bg-red-500/15 text-red-300",
    application: "bg-sky-500/15 text-sky-300",
    critical: "bg-purple-500/15 text-purple-300",
  };

  if (isLoading) return <LoadingSpinner text="Generating questions…" />;
  if (!data) return null;

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
      {(["easy", "medium", "hard", "application", "critical"] as const).map(level => (
        <div key={level} className="mb-6">
          <h3 className="section-title mb-3">
            <span className={`px-3 py-1 rounded-full text-xs capitalize ${diffColor[level]}`}>{level}</span>
            {" "}Questions
          </h3>
          <div className="space-y-2">
            {(data[level] || []).map((q: any, i: number) => {
              const key = `${level}-${i}`;
              return (
                <div key={i} className="glass-card p-4 cursor-pointer" onClick={() => setExpandedQ(expandedQ === key ? null : key)}>
                  <div className="flex items-start justify-between gap-4">
                    <p className="text-sm text-white leading-relaxed">{q.question}</p>
                    {expandedQ === key ? <ChevronUp size={14} className="shrink-0 text-slate-400 mt-0.5" /> : <ChevronDown size={14} className="shrink-0 text-slate-400 mt-0.5" />}
                  </div>
                  <AnimatePresence>
                    {expandedQ === key && (
                      <motion.p initial={{ height: 0, opacity: 0 }} animate={{ height: "auto", opacity: 1 }} exit={{ height: 0, opacity: 0 }}
                        className="text-xs text-slate-400 mt-2 border-t border-white/10 pt-2 overflow-hidden">
                        {q.context}
                      </motion.p>
                    )}
                  </AnimatePresence>
                </div>
              );
            })}
          </div>
        </div>
      ))}
    </motion.div>
  );
}

// ─── Multi-Doc Quiz Selector ──────────────────────────────────────────────────
function MultiDocQuiz({ onStart }: { onStart: (ids: number[], n: number) => void }) {
  const { data } = useQuery({ queryKey: ["documents"], queryFn: () => listDocuments().then(r => r.data) });
  const docs: any[] = data || [];
  const [selected, setSelected] = useState<number[]>([]);
  const [numQ, setNumQ] = useState(20);

  const toggle = (id: number) =>
    setSelected(prev => prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]);

  return (
    <div className="glass-card p-6">
      <h3 className="section-title mb-4"><FileText size={15} className="text-brand-400" /> Select Documents for Quiz</h3>
      {docs.length === 0 ? (
        <p className="text-slate-400 text-sm">No documents uploaded yet.</p>
      ) : (
        <div className="space-y-2 max-h-64 overflow-y-auto mb-5">
          {docs.map((d: any) => (
            <button key={d.id} onClick={() => toggle(d.id)}
              className={`w-full text-left px-4 py-3 rounded-xl border transition-all flex items-center gap-3 text-sm ${selected.includes(d.id) ? "border-brand-500/60 bg-brand-500/15 text-white" : "border-white/10 bg-white/5 text-slate-300 hover:bg-white/10"}`}>
              <div className={`w-4 h-4 rounded border flex items-center justify-center shrink-0 transition-all ${selected.includes(d.id) ? "bg-brand-500 border-brand-500" : "border-white/30"}`}>
                {selected.includes(d.id) && <CheckCircle size={10} className="text-white" />}
              </div>
              <span className="flex-1 truncate">{d.original_filename || d.filename}</span>
              <span className="text-xs text-slate-500">{d.word_count?.toLocaleString()} words</span>
            </button>
          ))}
        </div>
      )}

      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2 text-sm text-slate-400">
          <span>Questions:</span>
          <select value={numQ} onChange={e => setNumQ(Number(e.target.value))} className="input-field w-24 text-sm">
            {[10, 15, 20, 30, 40, 50].map(n => <option key={n} value={n}>{n}</option>)}
          </select>
        </div>
        <button
          onClick={() => onStart(selected, numQ)}
          disabled={selected.length < 2}
          className="btn-primary flex items-center gap-2 disabled:opacity-40"
        >
          <Zap size={14} /> Generate Multi-Doc Quiz ({selected.length} docs)
        </button>
      </div>
      {selected.length === 1 && <p className="text-xs text-amber-400 mt-2">Select at least 2 documents for a multi-doc quiz.</p>}
    </div>
  );
}

// ─── Main QuizPage ────────────────────────────────────────────────────────────
export function QuizPage() {
  const [searchParams] = useSearchParams();
  const [docId, setDocId] = useState<number | null>(
    searchParams.get("doc") ? Number(searchParams.get("doc")) : null
  );
  const [numQ, setNumQ] = useState(10);
  const [numCards, setNumCards] = useState(15);
  const [mode, setMode] = useState<Mode>("choose");
  const [fcMode, setFcMode] = useState<"flip" | "practice">("flip");
  const [quizAnswers, setQuizAnswers] = useState<Record<number, string>>({});
  const [quizKey, setQuizKey] = useState(0);
  const [multiMode, setMultiMode] = useState(false);
  const [multiQuizData, setMultiQuizData] = useState<any>(null);

  // Single-doc quiz & flashcards
  const { data: quizData, isLoading: quizLoading } = useQuery({
    queryKey: ["quiz", docId, numQ],
    queryFn: () => getQuiz(docId!, numQ).then(r => r.data),
    enabled: !!docId && !multiMode,
  });
  const { data: flashData, isLoading: flashLoading } = useQuery({
    queryKey: ["flashcards", docId, numCards],
    queryFn: () => getFlashcards(docId!, numCards).then(r => r.data),
    enabled: !!docId && !multiMode,
  });

  // Multi-doc quiz mutation
  const multiMut = useMutation({
    mutationFn: ({ ids, n }: { ids: number[]; n: number }) => multiDocumentQuiz(ids, n).then(r => r.data),
    onSuccess: (data) => { setMultiQuizData(data); setMode("quiz"); setQuizKey(k => k + 1); },
  });

  // Active questions
  const mcqs: MCQ[] = multiMode
    ? (multiQuizData?.quiz || multiQuizData?.mcq || [])
    : (quizData?.quiz || quizData?.mcq || []);
  const cards: Flashcard[] = flashData?.flashcards || [];

  const handleFinish = useCallback((answers: Record<number, string>) => {
    setQuizAnswers(answers);
    setMode("results");
    const score = mcqs.filter((q, i) => answers[i] === q.answer).length;
    if ((score / mcqs.length) >= 0.8) confetti({ particleCount: 120, spread: 80, origin: { y: 0.6 } });
  }, [mcqs]);

  const retryQuiz = () => { setQuizKey(k => k + 1); setQuizAnswers({}); setMode("quiz"); };

  const isLoading = quizLoading || flashLoading || multiMut.isPending;

  return (
    <div className="p-8">
      <PageHeader title="Quiz & Study" subtitle="MCQs, flashcards, practice mode, grading — single or multi-document" icon={<Zap size={22} />} />

      {/* Config bar */}
      {!multiMode && (
        <div className="glass-card p-4 mb-6 flex flex-wrap gap-4 items-end">
          <div className="flex-1 min-w-44">
            <label className="text-xs text-slate-400 mb-1 block">Document</label>
            <DocSelector value={docId} onChange={id => { setDocId(id); setMode("choose"); setMultiQuizData(null); }} />
          </div>
          <div>
            <label className="text-xs text-slate-400 mb-1 block">Quiz Questions</label>
            <select value={numQ} onChange={e => setNumQ(Number(e.target.value))} className="input-field w-32" disabled={!docId}>
              {[5, 10, 15, 20, 25, 30].map(n => <option key={n} value={n}>{n}</option>)}
            </select>
          </div>
          <div>
            <label className="text-xs text-slate-400 mb-1 block">Flashcards</label>
            <select value={numCards} onChange={e => setNumCards(Number(e.target.value))} className="input-field w-32" disabled={!docId}>
              {[5, 10, 15, 20, 30].map(n => <option key={n} value={n}>{n}</option>)}
            </select>
          </div>
          <button onClick={() => { setMultiMode(true); setMode("choose"); }} className="btn-ghost text-sm flex items-center gap-2">
            <Plus size={14} /> Multi-Doc Quiz
          </button>
        </div>
      )}

      {multiMode && (
        <div className="mb-6">
          <div className="flex items-center gap-3 mb-4">
            <button onClick={() => { setMultiMode(false); setMode("choose"); setMultiQuizData(null); }} className="btn-ghost text-sm flex items-center gap-1"><ChevronLeft size={14} /> Back to Single Doc</button>
            <h2 className="text-lg font-semibold text-white">Multi-Document Quiz</h2>
          </div>
          {mode === "choose" && <MultiDocQuiz onStart={(ids, n) => { setQuizKey(k => k + 1); multiMut.mutate({ ids, n }); }} />}
        </div>
      )}

      {isLoading && <LoadingSpinner text={multiMut.isPending ? "Generating multi-doc quiz…" : "Loading…"} />}

      {/* Mode chooser */}
      {!multiMode && docId && !isLoading && mode === "choose" && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {[
            { icon: ListChecks, title: "MCQ Quiz", desc: `${mcqs.length} multiple-choice questions`, color: "from-amber-500 to-orange-500", action: () => setMode("quiz"), disabled: mcqs.length === 0 },
            { icon: Layers, title: "Flashcards", desc: `${cards.length} cards — flip to study`, color: "from-purple-500 to-pink-500", action: () => { setFcMode("flip"); setMode("flashcards"); }, disabled: cards.length === 0 },
            { icon: Eye, title: "Practice Mode", desc: "Questions & answers side by side", color: "from-emerald-500 to-teal-500", action: () => { setFcMode("practice"); setMode("flashcards"); }, disabled: cards.length === 0 },
            { icon: BookOpen, title: "Study Questions", desc: "Open-ended questions by difficulty", color: "from-blue-500 to-cyan-500", action: () => setMode("study"), disabled: false },
          ].map(({ icon: Icon, title, desc, color, action, disabled }, i) => (
            <motion.div key={i} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.06 }}>
              <button onClick={action} disabled={disabled} className="glass-card p-6 text-left w-full hover:bg-white/8 transition-all hover:-translate-y-0.5 disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:translate-y-0">
                <div className={`w-11 h-11 rounded-xl bg-gradient-to-br ${color} flex items-center justify-center mb-4 shadow-lg`}><Icon size={20} className="text-white" /></div>
                <div className="font-semibold text-white mb-1">{title}</div>
                <div className="text-xs text-slate-400">{desc}</div>
              </button>
            </motion.div>
          ))}
        </motion.div>
      )}

      {!docId && !multiMode && (
        <div className="glass-card p-14 text-center">
          <Zap size={40} className="text-slate-600 mx-auto mb-4" />
          <p className="text-slate-400">Select a document above, or use Multi-Doc Quiz to combine several documents.</p>
        </div>
      )}

      {/* Quiz */}
      {mode === "quiz" && mcqs.length > 0 && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
          <div className="flex items-center gap-4 mb-5">
            <button onClick={() => setMode("choose")} className="btn-ghost text-sm flex items-center gap-1"><ChevronLeft size={14} /> Back</button>
            <h2 className="text-lg font-semibold text-white">
              {multiMode ? `Multi-Doc Quiz — ${mcqs.length} Questions` : `Quiz — ${mcqs.length} Questions`}
            </h2>
          </div>
          <MCQQuiz key={quizKey} questions={mcqs} onFinish={handleFinish} />
        </motion.div>
      )}

      {/* Results */}
      {mode === "results" && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
          <div className="flex items-center gap-4 mb-5">
            <button onClick={() => setMode("choose")} className="btn-ghost text-sm flex items-center gap-1"><ChevronLeft size={14} /> Back</button>
            <h2 className="text-lg font-semibold text-white">Your Results</h2>
          </div>
          <Results questions={mcqs} answers={quizAnswers} onRetry={retryQuiz} onFlashcards={() => { setFcMode("flip"); setMode("flashcards"); }} />
        </motion.div>
      )}

      {/* Flashcards / Practice */}
      {mode === "flashcards" && cards.length > 0 && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
          <div className="flex items-center gap-4 mb-5">
            <button onClick={() => setMode("choose")} className="btn-ghost text-sm flex items-center gap-1"><ChevronLeft size={14} /> Back</button>
            <div className="flex gap-2">
              {(["flip", "practice"] as const).map(m => (
                <button key={m} onClick={() => setFcMode(m)} className={`px-4 py-2 rounded-xl text-sm font-medium transition-all ${fcMode === m ? "bg-brand-600 text-white" : "bg-white/5 text-slate-400 hover:text-white"}`}>
                  {m === "flip" ? "Flip Mode" : "Practice Mode"}
                </button>
              ))}
            </div>
          </div>
          {fcMode === "flip" ? <FlashcardMode cards={cards} /> : <PracticeMode cards={cards} />}
        </motion.div>
      )}

      {/* Study Questions */}
      {mode === "study" && docId && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
          <div className="flex items-center gap-4 mb-5">
            <button onClick={() => setMode("choose")} className="btn-ghost text-sm flex items-center gap-1"><ChevronLeft size={14} /> Back</button>
            <h2 className="text-lg font-semibold text-white">Study Questions</h2>
          </div>
          <StudyQuestions docId={docId} />
        </motion.div>
      )}
    </div>
  );
}
