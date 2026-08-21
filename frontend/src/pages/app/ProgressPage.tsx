import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { TrendingUp, CheckCircle, Clock, Zap, Flame, Target } from "lucide-react";
import { RadarChart, Radar, PolarGrid, PolarAngleAxis, ResponsiveContainer, Tooltip, BarChart, Bar, XAxis, YAxis, Cell } from "recharts";
import { masteryColor, stateLabel, currentUserId, fetchProgress } from "../../services/adaptiveEngine";
import { CONCEPTS, getSubject } from "../../data/curriculum";
import { loadUser } from "../../store/userStore";
import type { ProgressStats } from "../../types/education";

const COLORS = ["#6366f1","#10b981","#f59e0b","#ef4444","#06b6d4","#8b5cf6"];

export function ProgressPage() {
  const user = loadUser();
  const [stats, setStats] = useState<ProgressStats>({
    totalConcepts: 0, masteredConcepts: 0, inProgressConcepts: 0, needsReviewConcepts: 0,
    totalQuizAttempts: 0, pyqsSolved: 0, totalStudyMinutes: 0, streak: 0, subjectMastery: [],
  });
  const [masteryRows, setMasteryRows] = useState<any[]>([]);
  const [extra, setExtra] = useState<{ accuracy: number; questionsAnswered: number; questionsCorrect: number; overallMastery: number; hasHistory: boolean }>({
    accuracy: 0, questionsAnswered: 0, questionsCorrect: 0, overallMastery: 0, hasHistory: true,
  });
  const [error, setError] = useState<string | null>(null);
  const userId = currentUserId(user);

  useEffect(() => {
    fetchProgress(userId)
      .then(d => {
        setStats({
          totalConcepts: d.totalConcepts ?? 0,
          masteredConcepts: d.masteredConcepts ?? 0,
          inProgressConcepts: d.inProgressConcepts ?? 0,
          needsReviewConcepts: d.needsReviewConcepts ?? 0,
          totalQuizAttempts: d.totalQuizAttempts ?? 0,
          pyqsSolved: d.pyqsSolved ?? 0,
          totalStudyMinutes: d.totalStudyMinutes ?? 0,
          streak: d.streak ?? 0,
          subjectMastery: d.subjectMastery ?? [],
        });
        setMasteryRows(d.concepts || []);
        setExtra({
          accuracy: d.accuracy ?? 0,
          questionsAnswered: d.questionsAnswered ?? 0,
          questionsCorrect: d.questionsCorrect ?? 0,
          overallMastery: d.overallMastery ?? 0,
          hasHistory: d.hasHistory ?? false,
        });
      })
      .catch(e => setError(e?.message || "Could not load progress"));
  }, [userId]);

  const subjectRadarData = stats.subjectMastery.map(sm => ({
    subject: getSubject(sm.subjectId)?.shortName ?? sm.subjectId,
    mastery: sm.mastery,
  }));

  const masteryBreakdown = [
    { name: "Mastered",    value: stats.masteredConcepts,     color: "#10b981" },
    { name: "In Progress", value: stats.inProgressConcepts,   color: "#6366f1" },
    { name: "Needs Review",value: stats.needsReviewConcepts,  color: "#f59e0b" },
    { name: "Not Started", value: stats.totalConcepts - stats.masteredConcepts - stats.inProgressConcepts - stats.needsReviewConcepts, color: "#334155" },
  ];

  return (
    <div className="p-6 lg:p-8 max-w-5xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white">Progress</h1>
        <p className="text-slate-400 text-sm mt-1">
          Your learning journey at a glance — every number below comes from your recorded attempts.
        </p>
        {error && <p className="text-sm text-red-300 mt-2">{error}</p>}
      </div>

      {!extra.hasHistory && !error && (
        <div className="bg-white/3 border border-white/6 rounded-2xl p-8 text-center mb-8">
          <p className="text-slate-300 font-medium">No study history yet</p>
          <p className="text-slate-500 text-sm mt-1">
            Take an adaptive quiz and your mastery, accuracy and charts will appear here.
          </p>
        </div>
      )}

      {/* Top stats */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 mb-8">
        {[
          { icon: CheckCircle, label: "Mastered",    value: stats.masteredConcepts,   color: "text-emerald-400" },
          { icon: Target,      label: "In Progress", value: stats.inProgressConcepts, color: "text-indigo-400"  },
          { icon: Zap,         label: "Quizzes",     value: stats.totalQuizAttempts,  color: "text-amber-400"  },
          { icon: TrendingUp,  label: "PYQs Solved", value: stats.pyqsSolved,         color: "text-blue-400"   },
          { icon: Clock,       label: "Study Time",  value: `${Math.round(stats.totalStudyMinutes/60)}h`, color: "text-purple-400" },
          { icon: Flame,       label: "Streak",      value: `${stats.streak}d`,       color: "text-orange-400" },
          { icon: Target,      label: "Accuracy",    value: `${extra.accuracy}%`,     color: "text-emerald-400" },
          { icon: Zap,         label: "Questions",   value: extra.questionsAnswered,  color: "text-indigo-400" },
          { icon: TrendingUp,  label: "Overall Mastery", value: `${extra.overallMastery}%`, color: "text-purple-400" },
        ].map(({ icon: Icon, label, value, color }, i) => (
          <motion.div key={label} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.05 }}
            className="bg-white/3 border border-white/6 rounded-2xl p-5 text-center">
            <Icon size={18} className={`${color} mx-auto mb-2`} />
            <div className={`text-2xl font-bold text-white`}>{value}</div>
            <div className="text-xs text-slate-500 mt-1">{label}</div>
          </motion.div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* Subject mastery radar */}
        <div className="bg-white/3 border border-white/6 rounded-2xl p-6">
          <h3 className="font-semibold text-white mb-5">Subject Mastery</h3>
          <ResponsiveContainer width="100%" height={260}>
            <RadarChart data={subjectRadarData}>
              <PolarGrid stroke="#1e1e3a" />
              <PolarAngleAxis dataKey="subject" tick={{ fill: "#94a3b8", fontSize: 11 }} />
              <Radar name="Mastery" dataKey="mastery" stroke="#6366f1" fill="#6366f1" fillOpacity={0.25} strokeWidth={2} />
              <Tooltip contentStyle={{ background: "#0d0d1a", border: "1px solid #1e1e3a", borderRadius: 12 }} />
            </RadarChart>
          </ResponsiveContainer>
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
                {masteryBreakdown.map((entry, i) => <Cell key={i} fill={entry.color} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Concept list */}
      <h3 className="font-semibold text-white mb-4">All Concepts</h3>
      <div className="space-y-2">
        {masteryRows.length === 0 && (
          <div className="bg-white/3 border border-white/6 rounded-xl p-6 text-center text-slate-500 text-sm">
            No concept mastery recorded yet.
          </div>
        )}
        {masteryRows.map((m, i) => {
          const concept = CONCEPTS.find(c => c.id === m.conceptId);
          const sub = concept ? getSubject(concept.subjectId) : null;
          if (!concept) return null;
          return (
            <motion.div key={m.conceptId} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: i * 0.04 }}
              className="bg-white/3 border border-white/6 rounded-xl p-4 flex items-center gap-4">
              <div className="flex-1 min-w-0">
                <div className="text-sm font-medium text-white">{concept.name}</div>
                <div className="text-xs text-slate-500 mt-0.5">
                  {sub?.name}{m.state ? ` · ${stateLabel(m.state)}` : ""}
                  {m.questionsAttempted ? ` · ${m.questionsCorrect}/${m.questionsAttempted} correct` : ""}
                </div>
              </div>
              <div className="w-28 bg-white/8 rounded-full h-2 shrink-0">
                <div className={`h-2 rounded-full transition-all ${m.score >= 80 ? "bg-emerald-500" : m.score >= 50 ? "bg-indigo-500" : m.score > 0 ? "bg-amber-500" : "bg-slate-700"}`}
                  style={{ width: `${m.score}%` }} />
              </div>
              <div className={`text-sm font-bold w-10 text-right shrink-0 ${masteryColor(m.score)}`}>{m.score > 0 ? `${m.score}%` : "—"}</div>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}
