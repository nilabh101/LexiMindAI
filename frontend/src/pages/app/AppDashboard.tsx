import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import {
  BookOpen, Zap, FileText, MessageCircle, ArrowRight,
  Flame, Target, Clock, CheckCircle, AlertCircle, BarChart3
} from "lucide-react";
import { loadUser } from "../../store/userStore";
import { getSubject } from "../../data/curriculum";
import {
  masteryColor, useAdaptive, currentUserId, currentSubjectId,
  fetchWeakConcepts, fetchDailyPlan, fetchProgress, fetchNextRecommendation,
  type DailyPlan, type Recommendation, type WeakConcept,
} from "../../services/adaptiveEngine";

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

const EMPTY_PLAN: DailyPlan = { studyMinutes: 0, plannedMinutes: 0, blocks: [], empty: true };

export function AppDashboard() {
  const user = loadUser();
  const userId = currentUserId(user);
  const subjectId = currentSubjectId(user);
  const dailyMinutes = user?.dailyStudyMinutes ?? 60;

  const progress = useAdaptive(() => fetchProgress(userId), [userId], null as any);
  const weak = useAdaptive<WeakConcept[]>(() => fetchWeakConcepts(userId, subjectId), [userId, subjectId], []);
  const plan = useAdaptive<DailyPlan>(
    () => fetchDailyPlan(userId, subjectId, dailyMinutes), [userId, subjectId, dailyMinutes], EMPTY_PLAN);
  const next = useAdaptive<Recommendation | null>(
    () => fetchNextRecommendation(userId, subjectId), [userId, subjectId], null);

  const stats = progress.data;
  const recommendation = next.data;
  const recommendedSubject = recommendation?.subjectId ? getSubject(recommendation.subjectId) : null;
  const streak = stats?.streak ?? 0;
  const studyMinutes = Math.round(stats?.totalStudyMinutes ?? 0);

  return (
    <div className="p-6 lg:p-8 max-w-6xl mx-auto">
      {/* Header */}
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="mb-8">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-bold text-white">
              {greeting()}, {(user?.name ?? "Student").split(" ")[0]} 👋
            </h1>
            <p className="text-slate-400 text-sm mt-1">
              {streak > 0
                ? <>You're on a <span className="text-amber-400 font-semibold">{streak}-day streak</span> — keep it going!</>
                : "Answer a few questions today to start a study streak."}
            </p>
          </div>
          <div className="flex items-center gap-2 bg-amber-500/10 border border-amber-500/20 px-3 py-2 rounded-xl">
            <Flame size={16} className="text-amber-400" />
            <span className="text-amber-300 font-bold text-sm">{streak}</span>
          </div>
        </div>
        {progress.error && <p className="text-sm text-red-300 mt-2">{progress.error}</p>}
      </motion.div>

      {/* Stats — all from the backend progress service */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <StatCard label="Concepts Mastered" value={stats?.masteredConcepts ?? 0}
          sub={`of ${stats?.totalConcepts ?? 0} in your syllabus`} color="text-emerald-400" icon={CheckCircle} />
        <StatCard label="In Progress" value={stats?.inProgressConcepts ?? 0} color="text-amber-400" icon={Target} />
        <StatCard label="Study Time" value={`${studyMinutes} min`} sub="recorded from quizzes" color="text-indigo-400" icon={Clock} />
        <StatCard label="Quizzes Taken" value={stats?.totalQuizAttempts ?? 0}
          sub={stats?.questionsAnswered ? `${stats.questionsAnswered} questions · ${stats.accuracy}% accuracy` : undefined}
          color="text-purple-400" icon={BarChart3} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        {/* Continue Learning — next recommendation from the engine */}
        <div className="lg:col-span-2">
          <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-3">Continue Learning</h2>
          {recommendation ? (
            <Link to={`/app/concepts/${recommendation.conceptId}`}>
              <div className="bg-gradient-to-br from-indigo-600/20 to-purple-600/10 border border-indigo-500/20 rounded-2xl p-6 hover:border-indigo-500/40 transition-all group">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <div className="w-12 h-12 rounded-xl bg-indigo-600/30 flex items-center justify-center text-2xl">
                      {recommendedSubject?.icon ?? "📚"}
                    </div>
                    <div>
                      <div className="font-semibold text-white text-lg">{recommendation.concept}</div>
                      <div className="text-sm text-slate-400">{recommendation.subject ?? recommendation.chapter}</div>
                    </div>
                  </div>
                  <span className="text-xs bg-amber-500/20 text-amber-300 border border-amber-500/20 px-2.5 py-1 rounded-lg">
                    {recommendation.type}
                  </span>
                </div>
                <p className="text-slate-400 text-sm mb-4">{recommendation.reason}</p>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 text-xs text-slate-500">
                    <Clock size={12} /> {recommendation.estimatedMinutes} min
                  </div>
                  <div className="flex items-center gap-1 text-indigo-400 text-sm font-medium group-hover:gap-2 transition-all">
                    Continue <ArrowRight size={14} />
                  </div>
                </div>
                <div className="mt-4 bg-white/5 rounded-full h-1.5">
                  <div className="bg-indigo-500 h-1.5 rounded-full" style={{ width: `${Math.max(recommendation.mastery, 2)}%` }} />
                </div>
                <div className="text-xs text-slate-500 mt-1">
                  {recommendation.mastery > 0
                    ? `${recommendation.mastery}% LexiMind Mastery Score`
                    : "Not attempted yet"}
                </div>
              </div>
            </Link>
          ) : (
            <div className="bg-white/3 border border-white/6 rounded-2xl p-8 text-center">
              <BookOpen size={32} className="text-slate-600 mx-auto mb-3" />
              <p className="text-slate-400">
                {next.loading ? "Loading your recommendation…" : "No recommendation yet — take a quiz so LexiMind can learn what you know."}
              </p>
              <Link to="/app/subjects" className="inline-flex items-center gap-1 text-indigo-400 text-sm mt-3 hover:gap-2 transition-all">
                Browse Subjects <ArrowRight size={13} />
              </Link>
            </div>
          )}
        </div>

        {/* Today's Plan — recommendation engine, respecting the user's study time */}
        <div>
          <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-3">
            Today's Plan {plan.data.plannedMinutes > 0 && <span className="text-slate-500 normal-case">· {plan.data.plannedMinutes} min</span>}
          </h2>
          <div className="bg-white/3 border border-white/6 rounded-2xl p-5 space-y-3">
            {plan.data.blocks.length === 0 ? (
              <p className="text-sm text-slate-500">
                {plan.loading ? "Building your plan…" : (plan.data.message || "Take a quiz to get a personalised plan.")}
              </p>
            ) : plan.data.blocks.map((block, i) => (
              <Link key={i} to={`/app/concepts/${block.conceptId}`} className="flex items-start gap-3 group">
                <div className="mt-0.5 w-5 h-5 rounded-full border border-white/15 flex items-center justify-center shrink-0 text-[9px] text-slate-400">
                  {block.minutes ?? block.estimatedMinutes}
                </div>
                <span className="text-sm leading-snug text-slate-300 group-hover:text-white transition-colors">
                  {block.title}
                  <span className="block text-xs text-slate-500 mt-0.5">{block.reason}</span>
                </span>
              </Link>
            ))}
          </div>
        </div>
      </div>

      {/* Weak areas + review schedule */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <div>
          <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-3">Needs Attention</h2>
          <div className="space-y-2">
            {weak.data.length === 0 ? (
              <div className="bg-white/3 border border-white/6 rounded-xl p-4 text-center text-slate-500 text-sm">
                {weak.loading ? "Checking your performance…" : "No weak concepts detected from your attempts yet."}
              </div>
            ) : weak.data.map((w) => (
              <Link key={w.conceptId} to={`/app/concepts/${w.conceptId}`}>
                <div className="bg-white/3 border border-white/6 rounded-xl p-4 flex items-start justify-between hover:bg-white/5 transition-all">
                  <div className="pr-3">
                    <div className="text-sm font-medium text-white">{w.concept}</div>
                    <div className="text-xs text-slate-500 mt-0.5">{w.reason}</div>
                  </div>
                  <div className="flex items-center gap-3 shrink-0">
                    <span className={`text-sm font-bold ${masteryColor(w.mastery)}`}>{w.mastery}%</span>
                    <AlertCircle size={14} className="text-amber-400" />
                  </div>
                </div>
              </Link>
            ))}
          </div>
        </div>

        <div>
          <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-3">Recent Activity</h2>
          <div className="space-y-2">
            {(stats?.recentSessions ?? []).length === 0 ? (
              <div className="bg-white/3 border border-white/6 rounded-xl p-4 text-center text-slate-500 text-sm">
                No quiz sessions recorded yet.
              </div>
            ) : (stats?.recentSessions ?? []).map((s: any, i: number) => (
              <div key={i} className="bg-white/3 border border-white/6 rounded-xl p-4 flex items-center gap-3">
                <span className="text-lg">⚡</span>
                <div className="flex-1">
                  <div className="text-sm font-medium text-white">
                    {getSubject(s.subjectId ?? "")?.name ?? "Quiz session"}
                  </div>
                  <div className="text-xs text-slate-500 mt-0.5">
                    {s.correct}/{s.total} correct · {new Date(s.completedAt).toLocaleDateString()}
                  </div>
                </div>
                <span className={`text-xs font-medium ${masteryColor(s.accuracy)}`}>{Math.round(s.accuracy)}%</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div>
        <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-3">Quick Actions</h2>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {[
            { to: "/app/notes",   icon: BookOpen,      label: "Study Notes",   color: "from-indigo-500 to-purple-500" },
            { to: "/app/quizzes", icon: Zap,           label: "Adaptive Quiz", color: "from-amber-500 to-orange-500" },
            { to: "/app/pyqs",    icon: FileText,      label: "Practice PYQs", color: "from-blue-500 to-cyan-500"   },
            { to: "/app/tutor",   icon: MessageCircle, label: "Ask AI Tutor",  color: "from-emerald-500 to-teal-500"},
          ].map(({ to, icon: Icon, label, color }) => (
            <Link key={to} to={to}
              className="bg-white/3 border border-white/6 rounded-2xl p-5 hover:bg-white/5 transition-all group text-center">
              <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${color} flex items-center justify-center mx-auto mb-3`}>
                <Icon size={18} className="text-white" />
              </div>
              <div className="text-sm font-medium text-slate-300 group-hover:text-white transition-colors">{label}</div>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}
