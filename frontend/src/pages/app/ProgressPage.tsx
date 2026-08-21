import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { TrendingUp, CheckCircle, Clock, Zap, Flame, Target, AlertTriangle } from "lucide-react";
import {
  RadarChart, Radar, PolarGrid, PolarAngleAxis, ResponsiveContainer,
  Tooltip, BarChart, Bar, XAxis, YAxis, Cell,
} from "recharts";
import { masteryColor } from "../../services/adaptiveEngine";
import { CONCEPTS, getSubject } from "../../data/curriculum";
import { getProgressApi, getWeakConceptsApi } from "../../lib/api";
import { loadUser } from "../../store/userStore";

const COLORS = ["#10b981","#6366f1","#f59e0b","#334155"];

export function ProgressPage() {
  const user = loadUser();
  const userId = user?.id || "demo-user-1";

  const [stats, setStats] = useState<any>(null);
  const [masteryRows, setMasteryRows] = useState<any[]>([]);
  const [weakConcepts, setWeakConcepts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [errors, setErrors] = useState<{ progress?: string; weak?: string }>({});

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      const [progRes, weakRes] = await Promise.allSettled([
        getProgressApi(userId),
        getWeakConceptsApi(userId),
      ]);
      if (cancelled) return;

      const newErrors: { progress?: string; weak?: string } = {};

      if (progRes.status === "fulfilled") {
        const d = progRes.value.data;
        setStats(d);
        setMasteryRows(d?.concepts || []);
      } else {
        newErrors.progress = "Could not load progress data.";
      }

      if (weakRes.status === "fulfilled") {
        setWeakConcepts(weakRes.value.data?.weakConcepts || []);
      } else {
        newErrors.weak = "Could not load weak concept data.";
      }

      setErrors(newErrors);
      setLoading(false);
    }
    load();
    return () => { cancelled = true; };
  }, [userId]);

  const hasData = stats && (stats.totalQuizAttempts ?? 0) >= 2;

  const subjectRadarData = (stats?.subjectMastery || []).map((sm: any) => ({
    subject: getSubject(sm.subjectId)?.shortName ?? sm.subjectId,
    mastery: sm.mastery,
  }));

  const masteryBreakdown = stats
    ? [
        { name: "Mastered",     value: stats.masteredConcepts,     color: "#10b981" },
        { name: "In Progress",  value: stats.inProgressConcepts,   color: "#6366f1" },
        { name: "Needs Review", value: stats.needsReviewConcepts,  color: "#f59e0b" },
        { name: "Not Started",
          value: Math.max(
            0,
            (stats.totalConcepts || 0) -
              (stats.masteredConcepts || 0) -
              (stats.inProgressConcepts || 0) -
              (stats.needsReviewConcepts || 0)
          ),
          color: "#334155",
        },
      ]
    : [];

  return (
    <div className="p-6 lg:p-8 max-w-5xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white">Progress</h1>
        <p className="text-slate-400 text-sm mt-1">Your learning journey at a glance.</p>
      </div>

      {/* Error banners */}
      {(errors.progress || errors.weak) && (
        <div className="mb-6 space-y-2">
          {errors.progress && (
            <div className="flex items-center gap-2 text-sm text-red-300 bg-red-500/10 border border-red-500/20 rounded-xl px-4 py-3">
              <AlertTriangle size={14} /> {errors.progress}
            </div>
          )}
          {errors.weak && (
            <div className="flex items-center gap-2 text-sm text-amber-300 bg-amber-500/10 border border-amber-500/20 rounded-xl px-4 py-3">
              <AlertTriangle size={14} /> {errors.weak}
            </div>
          )}
        </div>
      )}

      {/* Top stats */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 mb-8">
        {[
          { icon: CheckCircle, label: "Mastered",    value: stats?.masteredConcepts   ?? "—", color: "text-emerald-400" },
          { icon: Target,      label: "In Progress", value: stats?.inProgressConcepts ?? "—", color: "text-indigo-400"  },
          { icon: Zap,         label: "Quizzes",     value: stats?.totalQuizAttempts  ?? "—", color: "text-amber-400"  },
          { icon: TrendingUp,  label: "Accuracy",
            value: stats ? `${Math.round(stats.overallAccuracy ?? 0)}%` : "—",
            color: "text-blue-400"
          },
          { icon: Clock,
            label: "Questions",
            value: stats?.totalQuestionsAnswered ?? "—",
            color: "text-purple-400",
          },
          { icon: Flame,       label: "Streak",      value: stats ? `${stats.studyStreakDays ?? stats.streak ?? 0}d` : "—", color: "text-orange-400" },
        ].map(({ icon: Icon, label, value, color }, i) => (
          <motion.div
            key={label}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.05 }}
            className="bg-white/3 border border-white/6 rounded-2xl p-5 text-center"
          >
            <Icon size={18} className={`${color} mx-auto mb-2`} />
            <div className="text-2xl font-bold text-white">{loading ? "—" : value}</div>
            <div className="text-xs text-slate-500 mt-1">{label}</div>
          </motion.div>
        ))}
      </div>

      {/* Charts — only show when enough data */}
      {!hasData && !loading && (
        <div className="mb-8 bg-white/3 border border-white/6 rounded-2xl p-8 text-center">
          <BarChart3 size={32} className="text-slate-600 mx-auto mb-3" />
          <p className="text-slate-400 text-sm">
            Not enough data yet. Complete more quizzes to see your progress charts.
          </p>
        </div>
      )}

      {hasData && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* Subject mastery radar */}
          <div className="bg-white/3 border border-white/6 rounded-2xl p-6">
            <h3 className="font-semibold text-white mb-5">Subject Mastery</h3>
            {subjectRadarData.length > 0 ? (
              <ResponsiveContainer width="100%" height={260}>
                <RadarChart data={subjectRadarData}>
                  <PolarGrid stroke="#1e1e3a" />
                  <PolarAngleAxis dataKey="subject" tick={{ fill: "#94a3b8", fontSize: 11 }} />
                  <Radar name="Mastery" dataKey="mastery" stroke="#6366f1" fill="#6366f1" fillOpacity={0.25} strokeWidth={2} />
                  <Tooltip contentStyle={{ background: "#0d0d1a", border: "1px solid #1e1e3a", borderRadius: 12 }} />
                </RadarChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-64 flex items-center justify-center text-slate-500 text-sm">No subject data yet.</div>
            )}
          </div>

          {/* Mastery breakdown bar */}
          <div className="bg-white/3 border border-white/6 rounded-2xl p-6">
            <h3 className="font-semibold text-white mb-5">Concept Status</h3>
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={masteryBreakdown} layout="vertical" margin={{ left: 10 }}>
                <XAxis type="number" tick={{ fill: "#94a3b8", fontSize: 10 }} />
                <YAxis dataKey="name" type="category" tick={{ fill: "#94a3b8", fontSize: 11 }} width={90} />
                <Tooltip contentStyle={{ background: "#0d0d1a", border: "1px solid #1e1e3a", borderRadius: 12 }} />
                <Bar dataKey="value" radius={[0, 6, 6, 0]}>
                  {masteryBreakdown.map((entry: any, i: number) => (
                    <Cell key={i} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Recent performance */}
      {hasData && stats?.recentPerformance?.length > 0 && (
        <div className="mb-8">
          <h3 className="font-semibold text-white mb-4">Recent Performance</h3>
          <div className="space-y-2">
            {stats.recentPerformance.map((s: any, i: number) => (
              <div key={i} className="bg-white/3 border border-white/6 rounded-xl p-4 flex items-center gap-4">
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium text-white">
                    {getSubject(s.subjectId)?.name ?? s.subjectId ?? "Quiz"}
                  </div>
                  <div className="text-xs text-slate-500 mt-0.5">
                    {s.date ? new Date(s.date).toLocaleDateString() : ""}
                  </div>
                </div>
                <div className="text-sm font-bold text-white">{Math.round(s.score ?? 0)}%</div>
                <div className="text-xs text-slate-500">{s.correctCount}/{s.totalCount} correct</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Weak concepts from Phase 3 endpoint */}
      {weakConcepts.length > 0 && (
        <div className="mb-8">
          <h3 className="font-semibold text-white mb-4">Weak Concepts</h3>
          <div className="space-y-2">
            {weakConcepts.map((w: any, i: number) => {
              const score = w.masteryScore ?? 0;
              return (
                <div key={i} className="bg-white/3 border border-white/6 rounded-xl p-4 flex items-center gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-medium text-white truncate">
                      {w.conceptName || w.conceptId}
                    </div>
                    <div className="text-xs text-slate-500 mt-0.5 truncate">{w.reason}</div>
                  </div>
                  <div className="w-24 bg-white/8 rounded-full h-2 shrink-0">
                    <div
                      className="h-2 rounded-full bg-amber-500"
                      style={{ width: `${Math.min(score, 100)}%` }}
                    />
                  </div>
                  <div className={`text-sm font-bold w-10 text-right shrink-0 ${masteryColor(score)}`}>
                    {Math.round(score)}%
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* All concepts (from mastery rows) */}
      {masteryRows.length > 0 && (
        <>
          <h3 className="font-semibold text-white mb-4">All Concepts</h3>
          <div className="space-y-2">
            {masteryRows.map((m: any, i: number) => {
              const concept = CONCEPTS.find(
                c => c.id === (m.conceptId || m.concept_id)
              );
              const sub = concept ? getSubject(concept.subjectId) : null;
              const score = m.score ?? m.mastery_score ?? 0;
              const name = concept?.name || m.conceptId;
              return (
                <motion.div
                  key={m.conceptId || i}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: i * 0.03 }}
                  className="bg-white/3 border border-white/6 rounded-xl p-4 flex items-center gap-4"
                >
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-medium text-white truncate">{name}</div>
                    <div className="text-xs text-slate-500 mt-0.5">{sub?.name}</div>
                  </div>
                  <div className="w-28 bg-white/8 rounded-full h-2 shrink-0">
                    <div
                      className={`h-2 rounded-full transition-all ${
                        score >= 85 ? "bg-emerald-500" :
                        score >= 50 ? "bg-indigo-500" :
                        score > 0 ? "bg-amber-500" : "bg-slate-700"
                      }`}
                      style={{ width: `${Math.min(score, 100)}%` }}
                    />
                  </div>
                  <div className={`text-sm font-bold w-10 text-right shrink-0 ${masteryColor(score)}`}>
                    {score > 0 ? `${Math.round(score)}%` : "—"}
                  </div>
                </motion.div>
              );
            })}
          </div>
        </>
      )}

      {!loading && masteryRows.length === 0 && !errors.progress && (
        <div className="bg-white/3 border border-white/6 rounded-2xl p-8 text-center">
          <p className="text-slate-400 text-sm">
            No concept data yet. Take a quiz to start tracking your progress.
          </p>
        </div>
      )}
    </div>
  );
}

// fix missing import
function BarChart3({ size, className }: { size: number; className: string }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
    >
      <line x1="18" y1="20" x2="18" y2="10" />
      <line x1="12" y1="20" x2="12" y2="4" />
      <line x1="6" y1="20" x2="6" y2="14" />
      <line x1="2" y1="20" x2="22" y2="20" />
    </svg>
  );
}
