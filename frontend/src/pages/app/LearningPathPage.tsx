import { Link } from "react-router-dom";
import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { CheckCircle, Lock, Clock, ChevronRight, AlertCircle, Circle, Zap, Star } from "lucide-react";
import { masteryColor } from "../../services/adaptiveEngine";
import { getConcept, getSubject } from "../../data/curriculum";
import { getLearningPathApi, getRecommendedApi } from "../../lib/api";
import { loadUser } from "../../store/userStore";

type P3Status = "locked" | "available" | "in_progress" | "mastered" | "needs_review" | "COMPLETED" | "CURRENT" | "RECOMMENDED" | "LOCKED" | "NEEDS_REVIEW";

function normaliseStatus(s: string): string {
  const map: Record<string, string> = {
    COMPLETED: "mastered",
    CURRENT: "in_progress",
    RECOMMENDED: "available",
    LOCKED: "locked",
    NEEDS_REVIEW: "needs_review",
  };
  return map[s] || s;
}

const STATUS_CONFIG: Record<string, { color: string; bg: string; icon: React.ReactNode; label: string }> = {
  locked:       { color: "text-slate-500",   bg: "bg-slate-700/30 border-slate-600/30",     icon: <Lock size={14} />,          label: "Locked"       },
  available:    { color: "text-blue-300",    bg: "bg-blue-600/15 border-blue-500/30",       icon: <Circle size={14} />,        label: "Available"    },
  in_progress:  { color: "text-amber-300",   bg: "bg-amber-600/15 border-amber-500/30",     icon: <Zap size={14} />,           label: "In Progress"  },
  mastered:     { color: "text-emerald-300", bg: "bg-emerald-600/15 border-emerald-500/30", icon: <CheckCircle size={14} />,   label: "Mastered"     },
  needs_review: { color: "text-orange-300",  bg: "bg-orange-600/15 border-orange-500/30",   icon: <AlertCircle size={14} />,   label: "Needs Review" },
};
const FALLBACK_CONFIG = STATUS_CONFIG.available;

export function LearningPathPage() {
  const user = loadUser();
  const userId = user?.id || "demo-user-1";
  const subjectId = user?.academicProfile?.subjectIds?.[0] || "em1-btech";

  const [path, setPath] = useState<any[]>([]);
  const [recommendation, setRecommendation] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        setLoading(true);
        const [pathRes, recRes] = await Promise.allSettled([
          getLearningPathApi(userId, subjectId),
          getRecommendedApi(userId),
        ]);
        if (cancelled) return;

        if (pathRes.status === "fulfilled") {
          const items = pathRes.value.data?.items || [];
          setPath(items);
        } else {
          setError("Could not load learning path.");
        }

        if (recRes.status === "fulfilled") {
          setRecommendation(recRes.value.data?.recommendation || null);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => { cancelled = true; };
  }, [userId, subjectId]);

  return (
    <div className="p-6 lg:p-8 max-w-3xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white">Learning Path</h1>
        <p className="text-slate-400 text-sm mt-1">
          Your personalised roadmap — ordered by prerequisites and mastery.
        </p>
        {error && <p className="text-sm text-red-300 mt-2">{error}</p>}
      </div>

      {/* Next recommendation banner */}
      {recommendation && (
        <motion.div
          initial={{ opacity: 0, y: -8 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-6 bg-indigo-500/10 border border-indigo-500/25 rounded-2xl p-4 flex items-center justify-between gap-4"
        >
          <div>
            <div className="text-xs text-indigo-300 uppercase tracking-wider mb-0.5">Recommended Next</div>
            <div className="text-white font-semibold">{recommendation.conceptName}</div>
            <div className="text-slate-400 text-xs mt-0.5 line-clamp-1">{recommendation.reason}</div>
          </div>
          <Link
            to={`/app/quizzes`}
            className="shrink-0 flex items-center gap-1.5 bg-indigo-600 hover:bg-indigo-500 text-white text-xs px-3 py-2 rounded-xl transition-colors"
          >
            <Zap size={12} /> Practice
          </Link>
        </motion.div>
      )}

      {/* Status legend */}
      <div className="flex flex-wrap gap-3 mb-8">
        {Object.entries(STATUS_CONFIG).map(([status, cfg]) => (
          <span key={status} className={`flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-full border ${cfg.bg} ${cfg.color}`}>
            {cfg.icon} {cfg.label}
          </span>
        ))}
      </div>

      {/* Path nodes */}
      <div className="relative">
        <div className="absolute left-7 top-0 bottom-0 w-0.5 bg-gradient-to-b from-indigo-500/40 to-transparent" />

        {loading ? (
          <div className="space-y-4">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="flex gap-5 pl-2">
                <div className="w-10 h-10 rounded-full bg-white/5 animate-pulse shrink-0" />
                <div className="flex-1 h-24 bg-white/3 rounded-2xl animate-pulse border border-white/6" />
              </div>
            ))}
          </div>
        ) : path.length === 0 ? (
          <div className="bg-white/3 border border-white/6 rounded-2xl p-8 text-center">
            <p className="text-slate-400 text-sm">
              Your learning path will appear after your first quiz.
            </p>
            <Link to="/app/quizzes" className="inline-flex items-center gap-1 text-indigo-400 text-sm mt-3">
              Take a Quiz <ChevronRight size={13} />
            </Link>
          </div>
        ) : (
          <div className="space-y-4">
            {path.map((item: any, i: number) => {
              const status = normaliseStatus(item.status || "available");
              const cfg = STATUS_CONFIG[status] || FALLBACK_CONFIG;
              const concept = getConcept(item.conceptId);
              const subject = concept ? getSubject(concept.subjectId) : null;
              const isCurrentFocus = item.isCurrentFocus || item.status === "CURRENT";
              const isClickable = status !== "locked";
              const mastery = item.mastery ?? 0;

              const CardContent = (
                <motion.div
                  initial={{ opacity: 0, x: -12 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.06 }}
                  className={`relative flex gap-5 pl-2 ${isClickable ? "cursor-pointer" : "cursor-default"}`}
                >
                  {/* Node dot */}
                  <div className={`relative z-10 w-10 h-10 rounded-full border-2 flex items-center justify-center shrink-0 ${
                    isCurrentFocus
                      ? "bg-indigo-600 border-indigo-400 shadow-lg shadow-indigo-500/40"
                      : status === "mastered"
                      ? "bg-emerald-600/30 border-emerald-500/50"
                      : status === "locked"
                      ? "bg-slate-800 border-slate-700"
                      : "bg-white/5 border-white/15"
                  } ${cfg.color}`}>
                    {isCurrentFocus ? <Star size={14} className="text-indigo-200" /> : cfg.icon}
                  </div>

                  {/* Card */}
                  <div className={`flex-1 border rounded-2xl p-5 transition-all ${cfg.bg} ${
                    isCurrentFocus ? "ring-2 ring-indigo-500/30" : ""
                  } ${isClickable ? "hover:brightness-110" : ""}`}>
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex-1 min-w-0">
                        {isCurrentFocus && (
                          <span className="text-[10px] text-indigo-300 bg-indigo-500/20 px-2 py-0.5 rounded-full mb-2 inline-block">
                            Current Focus
                          </span>
                        )}
                        <div className={`font-semibold leading-snug ${status === "locked" ? "text-slate-500" : "text-white"}`}>
                          {concept?.name ?? item.conceptId}
                        </div>
                        {subject && <div className="text-xs text-slate-500 mt-0.5">{subject.name}</div>}
                        {concept?.description && (
                          <p className={`text-xs mt-1.5 line-clamp-1 ${status === "locked" ? "text-slate-600" : "text-slate-400"}`}>
                            {concept.description}
                          </p>
                        )}
                        {item.reason && (
                          <p className="text-xs text-slate-500 mt-1 italic">{item.reason}</p>
                        )}
                      </div>
                      <div className="shrink-0 text-right">
                        {mastery > 0 && (
                          <div className={`text-sm font-bold ${masteryColor(mastery)}`}>{mastery}%</div>
                        )}
                        <div className="text-xs text-slate-500 flex items-center gap-1 justify-end mt-1">
                          <Clock size={10} /> {item.estimatedMinutes ?? concept?.estimatedMinutes ?? 20}m
                        </div>
                      </div>
                    </div>

                    {mastery > 0 && (
                      <div className="mt-3 bg-black/20 rounded-full h-1">
                        <div className={`h-1 rounded-full ${
                          status === "mastered" ? "bg-emerald-500" :
                          status === "needs_review" ? "bg-orange-500" : "bg-indigo-500"
                        }`} style={{ width: `${Math.min(mastery, 100)}%` }} />
                      </div>
                    )}
                  </div>
                </motion.div>
              );

              return isClickable && concept ? (
                <Link key={item.id || item.conceptId} to={`/app/concepts/${item.conceptId}`}>
                  {CardContent}
                </Link>
              ) : (
                <div key={item.id || item.conceptId}>{CardContent}</div>
              );
            })}
          </div>
        )}
      </div>

      <div className="mt-8 p-5 bg-white/3 border border-white/6 rounded-2xl text-center">
        <p className="text-slate-400 text-sm">
          Your learning path updates automatically after each quiz.
        </p>
        <Link to="/app/quizzes" className="inline-flex items-center gap-1.5 text-indigo-400 text-sm mt-3 hover:text-indigo-300 transition-colors">
          Take a Quiz to Update Path <ChevronRight size={13} />
        </Link>
      </div>
    </div>
  );
}
