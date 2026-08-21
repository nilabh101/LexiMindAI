import { useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import {
  Zap, ChevronLeft, ChevronRight, CheckCircle, XCircle,
  RotateCcw, Trophy, ArrowRight, Clock
} from "lucide-react";
import { loadUser } from "../../store/userStore";
import { DEMO_USER } from "../../data/demoData";
import { getSubjectsByCourse, CONCEPTS } from "../../data/curriculum";

// Simple inline quiz experience without the old QuizPage complexity
const SAMPLE_QUESTIONS = [
  {
    id: "q1",
    conceptId: "euler-theorem-dc",
    question: "If f(x, y) = x³ + y³ + 3x²y, what is the degree of homogeneity?",
    options: ["2", "3", "4", "1"],
    answer: "3",
    explanation: "f(tx, ty) = t³x³ + t³y³ + 3t³x²y = t³f(x,y). So degree = 3.",
    difficulty: "medium",
  },
  {
    id: "q2",
    conceptId: "euler-theorem-dc",
    question: "Euler's theorem states: if f is homogeneous of degree n, then:",
    options: [
      "x·∂f/∂x + y·∂f/∂y = n·f",
      "x·∂f/∂x · y·∂f/∂y = n·f",
      "∂f/∂x + ∂f/∂y = n",
      "x + y = n·f",
    ],
    answer: "x·∂f/∂x + y·∂f/∂y = n·f",
    explanation: "This is the direct statement of Euler's theorem for homogeneous functions of degree n.",
    difficulty: "easy",
  },
  {
    id: "q3",
    conceptId: "partial-derivatives-dc",
    question: "For f(x,y) = x²y + y³, find ∂f/∂x:",
    options: ["2xy", "2xy + y³", "x² + 3y²", "2x + 3y²"],
    answer: "2xy",
    explanation: "Differentiate with respect to x, treating y as constant: ∂/∂x(x²y) = 2xy, ∂/∂x(y³) = 0.",
    difficulty: "easy",
  },
];

type QuizState = "setup" | "taking" | "results";

export function QuizzesPage() {
  const user = loadUser() ?? DEMO_USER;
  const subjects = getSubjectsByCourse(user.academicProfile?.courseId ?? "");

  const [quizState, setQuizState] = useState<QuizState>("setup");
  const [currentQ, setCurrentQ] = useState(0);
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [showExpl, setShowExpl] = useState(false);

  const q = SAMPLE_QUESTIONS[currentQ];
  const answered = answers[currentQ] !== undefined;
  const isCorrect = answered && answers[currentQ] === q.answer;

  const score = SAMPLE_QUESTIONS.filter((q, i) => answers[i] === q.answer).length;
  const pct = Math.round((score / SAMPLE_QUESTIONS.length) * 100);

  const pick = (opt: string) => {
    if (answered) return;
    setAnswers(p => ({ ...p, [currentQ]: opt }));
    setShowExpl(true);
  };

  const nextQ = () => {
    setShowExpl(false);
    if (currentQ < SAMPLE_QUESTIONS.length - 1) setCurrentQ(c => c + 1);
    else setQuizState("results");
  };

  const reset = () => { setQuizState("setup"); setCurrentQ(0); setAnswers({}); setShowExpl(false); };

  return (
    <div className="p-6 lg:p-8 max-w-3xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white">Quizzes</h1>
        <p className="text-slate-400 text-sm mt-1">Test your understanding concept by concept.</p>
      </div>

      <AnimatePresence mode="wait">
        {/* Setup screen */}
        {quizState === "setup" && (
          <motion.div key="setup" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
            <div className="bg-gradient-to-br from-indigo-600/15 to-purple-600/10 border border-indigo-500/15 rounded-3xl p-7 mb-6">
              <div className="flex items-center gap-4 mb-4">
                <div className="w-14 h-14 rounded-2xl bg-indigo-600/30 flex items-center justify-center text-2xl">📐</div>
                <div>
                  <div className="font-bold text-white text-xl">Euler's Theorem</div>
                  <div className="text-slate-400 text-sm">Engineering Mathematics I · 3 questions</div>
                </div>
              </div>
              <p className="text-slate-400 text-sm mb-6">Practice questions on Euler's theorem for homogeneous functions.</p>
              <div className="flex gap-4 text-sm text-slate-400 mb-6">
                <span className="flex items-center gap-1.5"><Zap size={13} /> 3 Questions</span>
                <span className="flex items-center gap-1.5"><Clock size={13} /> ~5 min</span>
              </div>
              <button onClick={() => setQuizState("taking")}
                className="bg-indigo-600 hover:bg-indigo-500 text-white px-6 py-3 rounded-xl font-semibold text-sm flex items-center gap-2 transition-all">
                Start Quiz <ArrowRight size={15} />
              </button>
            </div>

            {/* Subject quick-access */}
            <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-3">Browse by Subject</h2>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
              {subjects.slice(0, 6).map(sub => (
                <Link key={sub.id} to={`/app/subjects/${sub.id}`}
                  className="bg-white/3 border border-white/6 rounded-xl p-4 hover:bg-white/5 transition-all text-center">
                  <div className="text-2xl mb-2">{sub.icon}</div>
                  <div className="text-xs font-medium text-slate-300">{sub.shortName ?? sub.name}</div>
                </Link>
              ))}
            </div>
          </motion.div>
        )}

        {/* Taking quiz */}
        {quizState === "taking" && (
          <motion.div key="taking" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
            {/* Progress */}
            <div className="flex items-center gap-3 mb-6">
              <div className="flex-1 bg-white/8 rounded-full h-2">
                <div className="bg-indigo-500 h-2 rounded-full transition-all" style={{ width: `${((currentQ + 1) / SAMPLE_QUESTIONS.length) * 100}%` }} />
              </div>
              <span className="text-sm text-slate-400 shrink-0">{currentQ + 1}/{SAMPLE_QUESTIONS.length}</span>
            </div>

            <AnimatePresence mode="wait">
              <motion.div key={currentQ} initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }}
                className="bg-white/3 border border-white/6 rounded-3xl p-7">
                <div className="mb-6">
                  <span className={`text-xs px-2.5 py-1 rounded-full border mr-2 ${
                    q.difficulty === "easy" ? "bg-emerald-500/15 text-emerald-300 border-emerald-500/20" :
                    "bg-amber-500/15 text-amber-300 border-amber-500/20"
                  }`}>{q.difficulty}</span>
                  <p className="text-white font-semibold text-base leading-relaxed mt-3">{q.question}</p>
                </div>

                <div className="space-y-2.5">
                  {q.options.map((opt, i) => {
                    let cls = "border-white/8 bg-white/3 hover:bg-white/8 text-slate-200";
                    if (answered) {
                      if (opt === q.answer) cls = "border-emerald-500/50 bg-emerald-500/15 text-emerald-200";
                      else if (opt === answers[currentQ]) cls = "border-red-500/50 bg-red-500/15 text-red-300";
                      else cls = "border-white/5 bg-white/2 text-slate-500";
                    }
                    return (
                      <button key={i} onClick={() => pick(opt)} disabled={answered}
                        className={`w-full text-left px-4 py-3.5 rounded-xl border transition-all text-sm flex items-center gap-3 ${cls}`}>
                        <span className="w-6 h-6 rounded-full border border-current flex items-center justify-center text-xs font-bold shrink-0">
                          {String.fromCharCode(65 + i)}
                        </span>
                        <span className="flex-1 leading-snug">{opt}</span>
                        {answered && opt === q.answer && <CheckCircle size={14} className="text-emerald-400 shrink-0" />}
                        {answered && opt === answers[currentQ] && opt !== q.answer && <XCircle size={14} className="text-red-400 shrink-0" />}
                      </button>
                    );
                  })}
                </div>

                <AnimatePresence>
                  {showExpl && answered && (
                    <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: "auto" }} exit={{ opacity: 0, height: 0 }} className="overflow-hidden">
                      <div className={`mt-5 p-4 rounded-xl text-sm ${isCorrect ? "bg-emerald-500/10 border border-emerald-500/20 text-emerald-200" : "bg-red-500/10 border border-red-500/20 text-red-200"}`}>
                        <div className="font-semibold mb-1">{isCorrect ? "✓ Correct!" : "✗ Incorrect"}</div>
                        <p className="text-slate-300 text-xs leading-relaxed">{q.explanation}</p>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>

                <div className="flex items-center justify-between mt-6">
                  <button onClick={() => { setShowExpl(false); setCurrentQ(c => Math.max(0, c - 1)); }}
                    disabled={currentQ === 0} className="text-slate-400 hover:text-white text-sm flex items-center gap-1 disabled:opacity-30 transition-all">
                    <ChevronLeft size={15} /> Back
                  </button>
                  <button onClick={nextQ} disabled={!answered}
                    className="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 text-white px-5 py-2.5 rounded-xl text-sm font-semibold flex items-center gap-2 transition-all">
                    {currentQ === SAMPLE_QUESTIONS.length - 1 ? <><Trophy size={14} /> Finish</> : <>Next <ChevronRight size={14} /></>}
                  </button>
                </div>
              </motion.div>
            </AnimatePresence>
          </motion.div>
        )}

        {/* Results */}
        {quizState === "results" && (
          <motion.div key="results" initial={{ opacity: 0, scale: 0.97 }} animate={{ opacity: 1, scale: 1 }}>
            <div className="bg-white/3 border border-white/6 rounded-3xl p-8 text-center mb-6">
              <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center mx-auto mb-5">
                <Trophy size={28} className="text-white" />
              </div>
              <div className={`text-6xl font-black mb-2 ${pct >= 80 ? "text-emerald-400" : pct >= 60 ? "text-amber-400" : "text-red-400"}`}>{pct}%</div>
              <div className="text-white text-xl font-semibold mb-1">
                {pct >= 90 ? "Excellent!" : pct >= 75 ? "Good job!" : pct >= 60 ? "Keep going!" : "Needs practice"}
              </div>
              <div className="text-slate-400">{score}/{SAMPLE_QUESTIONS.length} correct</div>
              <div className="flex gap-3 justify-center mt-6">
                <button onClick={reset} className="flex items-center gap-2 text-sm text-slate-400 hover:text-white bg-white/5 px-5 py-2.5 rounded-xl transition-all"><RotateCcw size={13} /> Retry</button>
                <Link to="/app/learning-path" className="flex items-center gap-2 text-sm bg-indigo-600 hover:bg-indigo-500 text-white px-5 py-2.5 rounded-xl transition-all">
                  Update My Path <ArrowRight size={13} />
                </Link>
              </div>
            </div>

            {/* Review */}
            <div className="space-y-3">
              {SAMPLE_QUESTIONS.map((q, i) => {
                const correct = answers[i] === q.answer;
                return (
                  <div key={i} className="bg-white/3 border border-white/6 rounded-xl p-4">
                    <div className="flex items-start gap-3">
                      {correct ? <CheckCircle size={15} className="text-emerald-400 mt-0.5 shrink-0" /> : <XCircle size={15} className="text-red-400 mt-0.5 shrink-0" />}
                      <div>
                        <p className="text-sm text-white font-medium mb-1">{q.question}</p>
                        <div className="text-xs space-y-1">
                          {!correct && <div><span className="text-slate-500">Your answer: </span><span className="text-red-400">{answers[i] ?? "—"}</span></div>}
                          <div><span className="text-slate-500">Correct: </span><span className="text-emerald-400">{q.answer}</span></div>
                          <div className="mt-1.5 p-2 bg-white/5 rounded-lg text-slate-400">{q.explanation}</div>
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
