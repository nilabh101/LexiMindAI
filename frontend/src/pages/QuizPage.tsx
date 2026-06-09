import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { motion, AnimatePresence } from "framer-motion";
import { Zap, ChevronDown, ChevronUp, Check, X } from "lucide-react";
import { getQuiz, getQuestions } from "../lib/api";
import { DocSelector } from "../components/DocSelector";
import { LoadingSpinner } from "../components/LoadingSpinner";
import { PageHeader } from "../components/PageHeader";

export function QuizPage() {
  const [docId, setDocId] = useState<number | null>(null);
  const [tab, setTab] = useState<"quiz" | "questions">("quiz");
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [submitted, setSubmitted] = useState(false);
  const [expandedQ, setExpandedQ] = useState<number | null>(null);

  const { data: quizData, isLoading: quizLoading } = useQuery({
    queryKey: ["quiz", docId],
    queryFn: () => getQuiz(docId!).then(r => r.data),
    enabled: !!docId && tab === "quiz",
  });

  const { data: qData, isLoading: qLoading } = useQuery({
    queryKey: ["questions", docId],
    queryFn: () => getQuestions(docId!).then(r => r.data),
    enabled: !!docId && tab === "questions",
  });

  const mcqs: any[] = quizData?.mcq || [];
  const score = submitted
    ? mcqs.filter((q, i) => answers[i] === q.answer).length
    : null;

  const difficultyColor: Record<string, string> = {
    easy: "text-emerald-400 bg-emerald-400/10",
    medium: "text-amber-400 bg-amber-400/10",
    hard: "text-red-400 bg-red-400/10",
    application: "text-sky-400 bg-sky-400/10",
    critical: "text-purple-400 bg-purple-400/10",
  };

  return (
    <div className="p-8">
      <PageHeader
        title="Quiz & Question Generator"
        subtitle="AI-generated MCQs, true/false, and critical thinking questions"
        icon={<Zap size={22} />}
      />

      <div className="flex items-center gap-4 mb-6">
        <DocSelector value={docId} onChange={setDocId} className="flex-1 max-w-sm" />
        <div className="flex gap-2">
          {(["quiz", "questions"] as const).map(t => (
            <button key={t} onClick={() => { setTab(t); setSubmitted(false); setAnswers({}); }}
              className={`px-4 py-2 rounded-xl text-sm font-medium transition-all ${
                tab === t ? "bg-brand-600 text-white" : "bg-white/5 text-slate-400 hover:text-white"
              }`}>
              {t === "quiz" ? "Quiz (MCQ)" : "Questions"}
            </button>
          ))}
        </div>
      </div>

      {!docId && <div className="glass-card p-12 text-center text-slate-400">Select a document to generate quiz</div>}

      {/* MCQ Quiz */}
      {tab === "quiz" && docId && quizLoading && <LoadingSpinner text="Generating quiz…" />}
      {tab === "quiz" && quizData && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
          {submitted && score !== null && (
            <motion.div initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }}
              className="glass-card p-6 mb-6 bg-gradient-to-r from-emerald-500/10 to-teal-500/10 border border-emerald-500/20 text-center">
              <div className="text-4xl font-bold text-emerald-400">{score}/{mcqs.length}</div>
              <div className="text-slate-300 mt-1">Score: {Math.round((score / mcqs.length) * 100)}%</div>
            </motion.div>
          )}

          {/* MCQs */}
          <div className="space-y-4 mb-6">
            {mcqs.map((q: any, i: number) => (
              <motion.div key={i} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.05 }}
                className="glass-card p-5">
                <div className="flex items-start gap-3 mb-4">
                  <span className="text-brand-400 font-bold text-sm shrink-0">Q{i + 1}.</span>
                  <p className="text-sm text-white font-medium">{q.question}</p>
                  <span className={`ml-auto text-xs px-2 py-0.5 rounded-full shrink-0 ${difficultyColor[q.difficulty]}`}>
                    {q.difficulty}
                  </span>
                </div>
                <div className="grid grid-cols-2 gap-2">
                  {q.options.map((opt: string, j: number) => {
                    const isSelected = answers[i] === opt;
                    const isCorrect = submitted && opt === q.answer;
                    const isWrong = submitted && isSelected && opt !== q.answer;
                    return (
                      <button
                        key={j}
                        disabled={submitted}
                        onClick={() => setAnswers(prev => ({ ...prev, [i]: opt }))}
                        className={`text-left px-4 py-2.5 rounded-xl text-sm transition-all border
                          ${isCorrect ? "border-emerald-500 bg-emerald-500/20 text-emerald-300" :
                            isWrong ? "border-red-500 bg-red-500/20 text-red-300" :
                            isSelected ? "border-brand-500 bg-brand-500/20 text-brand-300" :
                            "border-white/10 bg-white/5 text-slate-300 hover:border-brand-500/50"}`}
                      >
                        <span className="font-medium mr-2">{String.fromCharCode(65 + j)}.</span>
                        {opt}
                        {isCorrect && <Check size={12} className="inline ml-2" />}
                        {isWrong && <X size={12} className="inline ml-2" />}
                      </button>
                    );
                  })}
                </div>
                {submitted && (
                  <p className="text-xs text-slate-400 mt-3 bg-white/5 rounded-lg p-2">{q.explanation}</p>
                )}
              </motion.div>
            ))}
          </div>

          {!submitted ? (
            <button
              onClick={() => setSubmitted(true)}
              disabled={Object.keys(answers).length < mcqs.length}
              className="btn-primary disabled:opacity-40"
            >
              Submit Quiz
            </button>
          ) : (
            <button onClick={() => { setAnswers({}); setSubmitted(false); }} className="btn-ghost">
              Reset
            </button>
          )}

          {/* T/F Questions */}
          <h3 className="section-title mt-8">True / False Questions</h3>
          <div className="space-y-3">
            {(quizData.true_false || []).map((q: any, i: number) => (
              <div key={i} className="glass-card p-4 flex items-start gap-4">
                <span className="text-xs px-2 py-0.5 rounded-full shrink-0 mt-0.5"
                  style={{ background: q.answer ? "#22c55e20" : "#ef444420", color: q.answer ? "#22c55e" : "#ef4444" }}>
                  {q.answer ? "TRUE" : "FALSE"}
                </span>
                <p className="text-sm text-slate-300">{q.question}</p>
              </div>
            ))}
          </div>
        </motion.div>
      )}

      {/* Questions Tab */}
      {tab === "questions" && docId && qLoading && <LoadingSpinner text="Generating questions…" />}
      {tab === "questions" && qData && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
          {(["easy", "medium", "hard", "application", "critical"] as const).map(level => (
            <div key={level} className="mb-6">
              <h3 className={`section-title capitalize`}>
                <span className={`px-3 py-1 rounded-full text-xs ${difficultyColor[level]}`}>{level}</span>
                &nbsp;Questions
              </h3>
              <div className="space-y-3">
                {(qData[level] || []).map((q: any, i: number) => (
                  <motion.div key={i} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: i * 0.05 }}
                    className="glass-card p-4 cursor-pointer"
                    onClick={() => setExpandedQ(expandedQ === i * 100 + level.length ? null : i * 100 + level.length)}
                  >
                    <div className="flex items-start justify-between gap-4">
                      <p className="text-sm text-white">{q.question}</p>
                      {expandedQ === i * 100 + level.length ? <ChevronUp size={14} className="shrink-0 text-slate-400" /> : <ChevronDown size={14} className="shrink-0 text-slate-400" />}
                    </div>
                    <AnimatePresence>
                      {expandedQ === i * 100 + level.length && (
                        <motion.p initial={{ height: 0, opacity: 0 }} animate={{ height: "auto", opacity: 1 }} exit={{ height: 0, opacity: 0 }}
                          className="text-xs text-slate-400 mt-2 border-t border-white/10 pt-2">
                          {q.context}
                        </motion.p>
                      )}
                    </AnimatePresence>
                  </motion.div>
                ))}
              </div>
            </div>
          ))}
        </motion.div>
      )}
    </div>
  );
}
