import { useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import {
  Zap, ChevronLeft, ChevronRight, CheckCircle, XCircle,
  RotateCcw, Trophy, ArrowRight, Clock
} from "lucide-react";
import { loadUser } from "../../store/userStore";
import { getSubjectsByCourse } from "../../data/curriculum";
import { generateAdaptiveQuiz, completeQuiz } from "../../lib/api";
import {
  currentUserId, currentSubjectId, masteryColor, stateLabel,
  type Recommendation,
} from "../../services/adaptiveEngine";

type QuizState = "setup" | "taking" | "results";

interface AdaptivePlan {
  conceptId?: string;
  concept?: string;
  mastery: number;
  state?: string;
  targetDifficulties: string[];
  selectionReason: string;
  prerequisiteNote?: string | null;
  message?: string | null;
  sourceCounts?: Record<string, number>;
}

export function QuizzesPage() {
  const user = loadUser();
  const userId = currentUserId(user);
  const subjectId = currentSubjectId(user);
  const [searchParams] = useSearchParams();
  const conceptId = searchParams.get("concept") || undefined;
  const subjects = getSubjectsByCourse(user?.academicProfile?.courseId ?? "");

  const [quizState, setQuizState] = useState<QuizState>("setup");
  const [currentQ, setCurrentQ] = useState(0);
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [showExpl, setShowExpl] = useState(false);
  const [questions, setQuestions] = useState<any[]>([]);
  const [quizId, setQuizId] = useState("quiz");
  const [loadError, setLoadError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [starting, setStarting] = useState(false);
  const [plan, setPlan] = useState<AdaptivePlan | null>(null);
  const [nextRecommendation, setNextRecommendation] = useState<Recommendation | null>(null);

  const q = questions[currentQ];
  const answered = answers[currentQ] !== undefined;
  const isCorrect = answered && q && (q.answer ? answers[currentQ] === q.answer : false);

  const score = questions.filter((qq, i) => qq.answer && answers[i] === qq.answer).length;
  const gradable = questions.filter(qq => qq.answer).length;
  const pct = gradable ? Math.round((score / gradable) * 100) : 0;

  const startQuiz = async () => {
    setLoadError(null);
    setStarting(true);
    try {
      const res = await generateAdaptiveQuiz({
        user_id: userId,
        subject_id: subjectId,
        concept_id: conceptId,
        question_count: 5,
      });
      const d = res.data;
      const qs = d.questions || [];
      setQuestions(qs);
      setQuizId(d.quiz_id || "quiz");
      setPlan({
        conceptId: d.concept_id,
        concept: d.concept,
        mastery: d.mastery ?? 0,
        state: d.state,
        targetDifficulties: d.target_difficulties || [],
        selectionReason: d.selection_reason || "",
        prerequisiteNote: d.prerequisite_note,
        message: d.message,
        sourceCounts: d.source_counts,
      });
      if (!qs.length) {
        setLoadError(d.message || "No questions in the bank for this concept yet. Upload notes or a PYQ PDF first.");
        return;
      }
      setQuizState("taking");
    } catch (e: any) {
      setLoadError(e?.message || "Could not generate quiz");
    } finally {
      setStarting(false);
    }
  };

  const pick = (opt: string) => {
    if (answered) return;
    setAnswers(p => ({ ...p, [currentQ]: opt }));
    setShowExpl(true);
  };

  const finish = async () => {
    setQuizState("results");
    setSaving(true);
    try {
      const res = await completeQuiz({
        user_id: userId,
        quiz_id: quizId,
        subject_id: subjectId,
        answers: questions.map((qq, i) => ({
          question_id: qq.id,
          selected_answer: answers[i],
          correct: qq.answer ? answers[i] === qq.answer : false,
          concept_id: qq.concept_id,
        })),
      });
      setNextRecommendation(res.data?.recommendation ?? null);
    } catch (e: any) {
      setLoadError(e?.message || "Your answers could not be saved.");
    } finally {
      setSaving(false);
    }
  };

  const nextQ = () => {
    setShowExpl(false);
    if (currentQ < questions.length - 1) setCurrentQ(c => c + 1);
    else finish();
  };

  const reset = () => {
    setQuizState("setup"); setCurrentQ(0); setAnswers({}); setShowExpl(false);
    setNextRecommendation(null); setLoadError(null);
  };

  return (
    <div className="p-6 lg:p-8 max-w-3xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white">Adaptive Quiz</h1>
        <p className="text-slate-400 text-sm mt-1">
          LexiMind picks the concept and difficulty from your mastery and recent answers.
        </p>
      </div>

      <AnimatePresence mode="wait">
        {/* Setup screen */}
        {quizState === "setup" && (
          <motion.div key="setup" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
            <div className="bg-gradient-to-br from-indigo-600/15 to-purple-600/10 border border-indigo-500/15 rounded-3xl p-7 mb-6">
              <div className="flex items-center gap-4 mb-4">
                <div className="w-14 h-14 rounded-2xl bg-indigo-600/30 flex items-center justify-center text-2xl">📐</div>
                <div>
                  <div className="font-bold text-white text-xl">
                    {plan?.concept ?? "Personalised quiz"}
                  </div>
                  <div className="text-slate-400 text-sm">
                    {plan
                      ? `${stateLabel(plan.state || "")} · LexiMind Mastery Score ${plan.mastery}`
                      : "The engine chooses your weakest ready concept."}
                  </div>
                </div>
              </div>
              <p className="text-slate-400 text-sm mb-4">
                {plan?.selectionReason ||
                  "Questions come from your uploaded PYQs and the question bank. Demo items are labeled DEMO."}
              </p>
              {plan?.prerequisiteNote && (
                <p className="text-amber-300/90 text-sm mb-4">{plan.prerequisiteNote}</p>
              )}
              <div className="flex gap-4 text-sm text-slate-400 mb-6">
                <span className="flex items-center gap-1.5"><Zap size={13} /> From question bank</span>
                <span className="flex items-center gap-1.5"><Clock size={13} /> ~5 min</span>
                {plan?.targetDifficulties?.length ? (
                  <span className="flex items-center gap-1.5">Target: {plan.targetDifficulties.join(" / ")}</span>
                ) : null}
              </div>
              {loadError && <p className="text-sm text-red-300 mb-4">{loadError}</p>}
              <button onClick={startQuiz} disabled={starting}
                className="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white px-6 py-3 rounded-xl font-semibold text-sm flex items-center gap-2 transition-all">
                {starting ? "Building your quiz…" : <>Start Adaptive Quiz <ArrowRight size={15} /></>}
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
            {(plan?.prerequisiteNote || plan?.message) && (
              <p className="text-amber-300/90 text-sm mb-4 bg-amber-500/10 border border-amber-500/20 rounded-xl px-4 py-3">
                {plan?.prerequisiteNote || plan?.message}
              </p>
            )}

            {/* Progress */}
            <div className="flex items-center gap-3 mb-6">
              <div className="flex-1 bg-white/8 rounded-full h-2">
                <div className="bg-indigo-500 h-2 rounded-full transition-all" style={{ width: `${((currentQ + 1) / Math.max(questions.length, 1)) * 100}%` }} />
              </div>
              <span className="text-sm text-slate-400 shrink-0">{currentQ + 1}/{questions.length}</span>
            </div>

            <AnimatePresence mode="wait">
              <motion.div key={currentQ} initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }}
                className="bg-white/3 border border-white/6 rounded-3xl p-7">
                <div className="mb-6">
                  <span className={`text-xs px-2.5 py-1 rounded-full border mr-2 ${
                    q?.difficulty === "easy" || q?.difficulty === "EASY" ? "bg-emerald-500/15 text-emerald-300 border-emerald-500/20" :
                    "bg-amber-500/15 text-amber-300 border-amber-500/20"
                  }`}>{q?.difficulty || "unknown"}</span>
                  {q?.source && <span className="text-xs px-2.5 py-1 rounded-full border border-white/10 text-slate-400">{q.source}</span>}
                  <p className="text-white font-semibold text-base leading-relaxed mt-3">{q?.question}</p>
                </div>

                <div className="space-y-2.5">
                  {(q?.options || []).length === 0 && (
                    <input
                      className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-sm text-white outline-none"
                      placeholder={q?.answer ? "Type your answer" : "No answer key stored — mark as reviewed to continue"}
                      value={answers[currentQ] || ""}
                      onChange={e => setAnswers(p => ({ ...p, [currentQ]: e.target.value }))}
                    />
                  )}
                  {(q?.options || []).map((opt: string, i: number) => {
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
                  <button onClick={nextQ} disabled={!answered && (q?.options || []).length > 0}
                    className="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 text-white px-5 py-2.5 rounded-xl text-sm font-semibold flex items-center gap-2 transition-all">
                    {currentQ === questions.length - 1 ? <><Trophy size={14} /> Finish</> : <>Next <ChevronRight size={14} /></>}
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
              <div className="text-slate-400">{score}/{gradable} scored{saving ? " · saving…" : ""}</div>
              {loadError && <p className="text-sm text-red-300 mt-2">{loadError}</p>}
              {nextRecommendation && (
                <Link to={`/app/concepts/${nextRecommendation.conceptId}`}
                  className="block mt-6 text-left bg-white/4 border border-white/8 rounded-2xl p-4 hover:bg-white/6 transition-all">
                  <div className="text-xs uppercase tracking-wider text-slate-500 mb-1">Recommended next</div>
                  <div className="text-white font-semibold text-sm">{nextRecommendation.title}</div>
                  <div className="text-xs text-slate-400 mt-1">{nextRecommendation.reason}</div>
                  <div className="text-xs text-slate-500 mt-1">
                    ~{nextRecommendation.estimatedMinutes} min · current mastery{" "}
                    <span className={masteryColor(nextRecommendation.mastery)}>{nextRecommendation.mastery}%</span>
                  </div>
                </Link>
              )}
              <div className="flex gap-3 justify-center mt-6">
                <button onClick={reset} className="flex items-center gap-2 text-sm text-slate-400 hover:text-white bg-white/5 px-5 py-2.5 rounded-xl transition-all"><RotateCcw size={13} /> Retry</button>
                <Link to="/app/learning-path" className="flex items-center gap-2 text-sm bg-indigo-600 hover:bg-indigo-500 text-white px-5 py-2.5 rounded-xl transition-all">
                  Update My Path <ArrowRight size={13} />
                </Link>
              </div>
            </div>

            {/* Review */}
            <div className="space-y-3">
              {questions.map((qq, i) => {
                const correct = qq.answer ? answers[i] === qq.answer : false;
                return (
                  <div key={i} className="bg-white/3 border border-white/6 rounded-xl p-4">
                    <div className="flex items-start gap-3">
                      {correct ? <CheckCircle size={15} className="text-emerald-400 mt-0.5 shrink-0" /> : <XCircle size={15} className="text-red-400 mt-0.5 shrink-0" />}
                      <div>
                        <p className="text-sm text-white font-medium mb-1">{qq.question}</p>
                        <div className="text-xs space-y-1">
                          <div className="text-slate-500">{qq.source}{qq.is_demo ? " · DEMO" : ""}</div>
                          {!correct && <div><span className="text-slate-500">Your answer: </span><span className="text-red-400">{answers[i] ?? "—"}</span></div>}
                          <div><span className="text-slate-500">Correct: </span><span className="text-emerald-400">{qq.answer ?? "unknown"}</span></div>
                          {qq.explanation && <div className="mt-1.5 p-2 bg-white/5 rounded-lg text-slate-400">{qq.explanation}</div>}
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
