import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import {
  BookOpen, Zap, FileText, MessageCircle, ArrowRight,
  Flame, Target, Clock, CheckCircle, AlertCircle, BarChart3,
  RefreshCw,
} from "lucide-react";
import { loadUser } from "../../store/userStore";
import { CONCEPTS, getSubject } from "../../data/curriculum";
import { masteryColor } from "../../services/adaptiveEngine";
import {
  getProgressApi, getWeakConceptsApi, getRecommendedApi, getDailyPlanApi,
} from "../../lib/api";

function greeting() {
  const h = new Date().getHours();
  if (h < 12) return "Good morning";
  if (h < 17) return "Good afternoon";
  return "Good evening";
}

function StatCard({ label, value, sub, color, icon: Icon }: any) {
  return (
    <div className="bg-white/3 border border-white/6 rounded-2xl p-5">
      <div className={`${color} mb-3`}><Icon size={18} /></div>
      <div className="text-2xl font-bold text-white">{value}</div>
      {sub && <div className="text-xs text-slate-500 mt-0.5">{sub}</div>}
      <div className="text-xs text-slate-400 mt-1">{label}</div>
    </div>
  );
}

export function AppDashboard() {
  const user = loadUser();
  const userId = user?.id || "demo-user-1";

  const [progress, setProgress] = useState<any>(null);
  const [weakConcepts, setWeakConcepts] = useState<any[]>([]);
  const [recommendation, setRecommendation] = useState<any>(null);
  const [dailyPlan, setDailyPlan] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        setLoading(true);
        const [progRes, weakRes, recRes, planRes] = await Promise.allSettled([
          getProgressApi(userId),
          getWeakConceptsApi(userId),
          getRecommendedApi(userId),
          getDailyPlanApi(userId, 30),
        ]);
        if (cancelled) return;

        if (progRes.status === "fulfilled") setProgress(progRes.value.data);
        if (weakRes.status === "fulfilled")
          setWeakConcepts(weakRes.value.data?.weakConcepts || []);
        if (recRes.status === "fulfilled")
          setRecommendation(recRes.value.data?.recommendation || null);
        if (planRes.status === "fulfilled")
          setDailyPlan(planRes.value.data?.activities || []);
      } catch (e: any) {
        if (!cancelled) setError(e?.message || "Could not load dashboard");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => { cancelled = true; };
  }, [userId]);

  const hasData = progress && (progress.totalQuizAttempts > 0 || progress.masteredConcepts > 0);

  // Current concept from recommendation
  const recConceptId = recommendation?.conceptId;
  const currentConcept = recConceptId ? CONCEPTS.find(c => c.id === recConceptId) : null;
  const currentSubject = currentConcept ? getSubject(currentConcept.subjectId) : null;
  const masteryForCurrent = recConceptId
    ? (progress?.concepts || []).find((m: any) => m.conceptId === recConceptId)
    : null;
  const currentMastery = masteryForCurrent?.score ?? masteryForCurrent?.mastery_score ?? 0;

  return (
    <div className="p-6 lg:p-8 max-w-6xl mx-auto">
      {/* Header */}
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="mb-8">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-bold text-white">
              {greeting()}, {(user?.name || "Learner").split(" ")[0]} 👋
            </h1>
            <p className="text-slate-400 text-sm mt-1">
              {hasData
                ? `${progress.masteredConcepts} concept${progress.masteredConcepts !== 1 ? "s" : ""} mastered — keep it going!`
                : "Start your first quiz to personalise this dashboard."}
            </p>
          </div>
          {loading && (
            <div className="flex items-center gap-1.5 text-slate-500 text-xs">
              <RefreshCw size={12} className="animate-spin" /> Loading
            </div>
          )}
        </div>
        {error && <p className="text-sm text-red-300 mt-2">{error}</p>}
      </motion.div>

      {/* Empty state for new users */}
      {!loading && !hasData && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="mb-8 bg-indigo-500/10 border border-indigo-500/20 rounded-2xl p-8 text-center"
        >
          <BookOpen size={36} className="text-indigo-400 mx-auto mb-3" />
          <h2 className="text-white font-semibold text-lg mb-2">Welcome to LexiMind AI</h2>
          <p className="text-slate-400 text-sm max-w-md mx-auto mb-6">
            Complete your first quiz to see your personalised dashboard — mastery scores, weak areas, today's plan, and recommendations.
          </p>
          <Link
            to="/app/quizzes"
            className="inline-flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500 text-white px-6 py-2.5 rounded-xl text-sm font-medium transition-colors"
          >
            <Zap size={14} /> Take Your First Quiz
          </Link>
        </motion.div>
      )}

      {/* Stats — only show when data exists */}
      {hasData && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <StatCard
            label="Concepts Mastered"
            value={progress.masteredConcepts}
            sub={`of ${progress.totalConcepts} total`}
            color="text-emerald-400"
            icon={CheckCircle}
          />
          <StatCard
            label="In Progress"
            value={progress.inProgressConcepts}
            color="text-amber-400"
            icon={Target}
          />
          <StatCard
            label="Accuracy"
            value={`${Math.round(progress.overallAccuracy ?? 0)}%`}
            sub="overall"
            color="text-indigo-400"
            icon={BarChart3}
          />
          <StatCard
            label="Quizzes Taken"
            value={progress.totalQuizAttempts}
            color="text-purple-400"
            icon={Zap}
          />
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        {/* Continue Learning */}
        <div className="lg:col-span-2">
          <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-3">Continue Learning</h2>
          {recommendation && currentConcept ? (
            <Link to={`/app/concepts/${currentConcept.id}`}>
              <div className="bg-gradient-to-br from-indigo-600/20 to-purple-600/10 border border-indigo-500/20 rounded-2xl p-6 hover:border-indigo-500/40 transition-all group">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <div className="w-12 h-12 rounded-xl bg-indigo-600/30 flex items-center justify-center text-2xl">
                      {currentSubject?.icon ?? "📚"}
                    </div>
                    <div>
                      <div className="font-semibold text-white text-lg">{currentConcept.name}</div>
                      <div className="text-sm text-slate-400">{currentSubject?.name}</div>
                    </div>
                  </div>
                  <span className="text-xs bg-indigo-500/20 text-indigo-300 border border-indigo-500/20 px-2.5 py-1 rounded-lg capitalize">
                    {recommendation.type?.toLowerCase() || "study"}
                  </span>
                </div>
                <p className="text-slate-400 text-sm mb-4 line-clamp-2">
                  {recommendation.reason || currentConcept.description}
                </p>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 text-xs text-slate-500">
                    <Clock size={12} /> {recommendation.estimatedMinutes ?? currentConcept.estimatedMinutes} min
                  </div>
                  <div className="flex items-center gap-1 text-indigo-400 text-sm font-medium group-hover:gap-2 transition-all">
                    Continue <ArrowRight size={14} />
                  </div>
                </div>
                {currentMastery > 0 && (
                  <>
                    <div className="mt-4 bg-white/5 rounded-full h-1.5">
                      <div
                        className="bg-indigo-500 h-1.5 rounded-full"
                        style={{ width: `${Math.min(currentMastery, 100)}%` }}
                      />
                    </div>
                    <div className={`text-xs mt-1 ${masteryColor(currentMastery)}`}>
                      {Math.round(currentMastery)}% mastery
                    </div>
                  </>
                )}
              </div>
            </Link>
          ) : !loading ? (
            <div className="bg-white/3 border border-white/6 rounded-2xl p-8 text-center">
              <BookOpen size={32} className="text-slate-600 mx-auto mb-3" />
              <p className="text-slate-400">No recommendation yet. Take a quiz to get started.</p>
              <Link to="/app/subjects" className="inline-flex items-center gap-1 text-indigo-400 text-sm mt-3 hover:gap-2 transition-all">
                Browse Subjects <ArrowRight size={13} />
              </Link>
            </div>
          ) : (
            <div className="bg-white/3 border border-white/6 rounded-2xl p-8 animate-pulse h-48" />
          )}
        </div>

        {/* Today's Plan */}
        <div>
          <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-3">Today's Plan</h2>
          <div className="bg-white/3 border border-white/6 rounded-2xl p-5 space-y-3">
            {loading ? (
              Array.from({ length: 3 }).map((_, i) => (
                <div key={i} className="h-8 bg-white/5 rounded animate-pulse" />
              ))
            ) : dailyPlan.length > 0 ? (
              dailyPlan.map((item: any, i: number) => (
                <div key={i} className="flex items-start gap-3">
                  <div className="mt-0.5 w-5 h-5 rounded-full border border-white/15 flex items-center justify-center shrink-0">
                    <span className="text-[9px] text-slate-400">{item.durationMinutes}m</span>
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="text-sm text-slate-300 leading-snug truncate">{item.conceptName}</div>
                    <div className="text-xs text-slate-500 capitalize">{item.type?.toLowerCase()}</div>
                  </div>
                </div>
              ))
            ) : (
              <p className="text-slate-500 text-sm text-center py-4">
                Complete a quiz to generate your plan.
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Weak Areas + Quick Actions */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* Weak Areas */}
        <div>
          <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-3">Needs Attention</h2>
          <div className="space-y-2">
            {loading ? (
              Array.from({ length: 2 }).map((_, i) => (
                <div key={i} className="h-16 bg-white/3 border border-white/6 rounded-xl animate-pulse" />
              ))
            ) : weakConcepts.length === 0 ? (
              <div className="bg-white/3 border border-white/6 rounded-xl p-4 text-center text-slate-500 text-sm">
                {hasData ? "All good! No weak areas." : "Take a quiz to identify weak areas."}
              </div>
            ) : (
              weakConcepts.slice(0, 3).map((w: any, i: number) => {
                const concept = CONCEPTS.find(c => c.id === w.conceptId);
                const sub = concept ? getSubject(concept.subjectId) : null;
                const score = w.masteryScore ?? 0;
                return (
                  <Link key={i} to={`/app/concepts/${w.conceptId}`}>
                    <div className="bg-white/3 border border-white/6 rounded-xl p-4 flex items-center justify-between hover:bg-white/5 transition-all">
                      <div className="min-w-0 flex-1">
                        <div className="text-sm font-medium text-white truncate">
                          {w.conceptName || concept?.name || w.conceptId}
                        </div>
                        <div className="text-xs text-slate-500 mt-0.5 truncate">
                          {sub?.name || w.reason}
                        </div>
                      </div>
                      <div className="flex items-center gap-3 shrink-0 ml-3">
                        <span className={`text-sm font-bold ${masteryColor(score)}`}>
                          {Math.round(score)}%
                        </span>
                        <AlertCircle size={14} className="text-amber-400" />
                      </div>
                    </div>
                  </Link>
                );
              })
            )}
          </div>
        </div>

        {/* Quick Actions */}
        <div>
          <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-3">Quick Actions</h2>
          <div className="grid grid-cols-2 gap-3">
            {[
              { to: "/app/notes",   icon: BookOpen,      label: "Study Notes",   color: "from-indigo-500 to-purple-500" },
              { to: "/app/quizzes", icon: Zap,           label: "Take Quiz",     color: "from-amber-500 to-orange-500" },
              { to: "/app/pyqs",    icon: FileText,      label: "Practice PYQs", color: "from-blue-500 to-cyan-500"   },
              { to: "/app/tutor",   icon: MessageCircle, label: "Ask AI Tutor",  color: "from-emerald-500 to-teal-500"},
            ].map(({ to, icon: Icon, label, color }) => (
              <Link
                key={to}
                to={to}
                className="bg-white/3 border border-white/6 rounded-2xl p-5 hover:bg-white/5 transition-all group text-center"
              >
                <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${color} flex items-center justify-center mx-auto mb-3`}>
                  <Icon size={18} className="text-white" />
                </div>
                <div className="text-sm font-medium text-slate-300 group-hover:text-white transition-colors">
                  {label}
                </div>
              </Link>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
