import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { CheckCircle, Lock, Clock, ChevronRight, AlertCircle, Circle, Zap } from "lucide-react";
import { getLearningPath, masteryColor } from "../../services/adaptiveEngine";
import { getConcept, getSubject } from "../../data/curriculum";
import type { LearningPathItemStatus } from "../../types/education";

const STATUS_CONFIG: Record<LearningPathItemStatus, { color: string; bg: string; icon: React.ReactNode; label: string }> = {
  locked:      { color: "text-slate-500",  bg: "bg-slate-700/30 border-slate-600/30",    icon: <Lock size={14} />,          label: "Locked" },
  available:   { color: "text-blue-300",   bg: "bg-blue-600/15 border-blue-500/30",      icon: <Circle size={14} />,        label: "Available" },
  in_progress: { color: "text-amber-300",  bg: "bg-amber-600/15 border-amber-500/30",    icon: <Zap size={14} />,           label: "In Progress" },
  mastered:    { color: "text-emerald-300",bg: "bg-emerald-600/15 border-emerald-500/30",icon: <CheckCircle size={14} />,   label: "Mastered" },
  needs_review:{ color: "text-orange-300", bg: "bg-orange-600/15 border-orange-500/30",  icon: <AlertCircle size={14} />,   label: "Needs Review" },
};

export function LearningPathPage() {
  const path = getLearningPath();

  return (
    <div className="p-6 lg:p-8 max-w-3xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white">Learning Path</h1>
        <p className="text-slate-400 text-sm mt-1">
          Your personalised roadmap. Concepts are ordered by prerequisites and your mastery.
        </p>
      </div>

      {/* Legend */}
      <div className="flex flex-wrap gap-3 mb-8">
        {Object.entries(STATUS_CONFIG).map(([status, cfg]) => (
          <span key={status} className={`flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-full border ${cfg.bg} ${cfg.color}`}>
            {cfg.icon} {cfg.label}
          </span>
        ))}
      </div>

      {/* Path nodes */}
      <div className="relative">
        {/* Vertical line */}
        <div className="absolute left-7 top-0 bottom-0 w-0.5 bg-gradient-to-b from-indigo-500/40 to-transparent" />

        <div className="space-y-4">
          {path.map((item, i) => {
            const concept = getConcept(item.conceptId);
            const subject = concept ? getSubject(concept.subjectId) : null;
            const cfg = STATUS_CONFIG[item.status];
            const isClickable = item.status !== "locked";

            const CardContent = (
              <motion.div
                initial={{ opacity: 0, x: -12 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.07 }}
                className={`relative flex gap-5 pl-2 ${isClickable ? "cursor-pointer" : "cursor-default"}`}>
                {/* Node dot */}
                <div className={`relative z-10 w-10 h-10 rounded-full border-2 flex items-center justify-center shrink-0 ${
                  item.isCurrentFocus
                    ? "bg-indigo-600 border-indigo-400 shadow-lg shadow-indigo-500/40"
                    : item.status === "mastered"
                    ? "bg-emerald-600/30 border-emerald-500/50"
                    : item.status === "locked"
                    ? "bg-slate-800 border-slate-700"
                    : "bg-white/5 border-white/15"
                } ${cfg.color}`}>
                  {cfg.icon}
                </div>

                {/* Card */}
                <div className={`flex-1 border rounded-2xl p-5 transition-all ${cfg.bg} ${
                  item.isCurrentFocus ? "ring-2 ring-indigo-500/30" : ""
                } ${isClickable ? "hover:brightness-110" : ""}`}>
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex-1">
                      {item.isCurrentFocus && (
                        <span className="text-[10px] text-indigo-300 bg-indigo-500/20 px-2 py-0.5 rounded-full mb-2 inline-block">
                          Current Focus
                        </span>
                      )}
                      <div className={`font-semibold ${item.status === "locked" ? "text-slate-500" : "text-white"} leading-snug`}>
                        {concept?.name ?? item.conceptId}
                      </div>
                      {subject && <div className="text-xs text-slate-500 mt-0.5">{subject.name}</div>}
                      {concept?.description && (
                        <p className={`text-xs mt-1.5 line-clamp-1 ${item.status === "locked" ? "text-slate-600" : "text-slate-400"}`}>
                          {concept.description}
                        </p>
                      )}
                    </div>
                    <div className="shrink-0 text-right">
                      {item.mastery > 0 && (
                        <div className={`text-sm font-bold ${masteryColor(item.mastery)}`}>{item.mastery}%</div>
                      )}
                      <div className="text-xs text-slate-500 flex items-center gap-1 justify-end mt-1">
                        <Clock size={10} /> {item.estimatedMinutes}m
                      </div>
                    </div>
                  </div>

                  {/* Mastery bar */}
                  {item.mastery > 0 && (
                    <div className="mt-3 bg-black/20 rounded-full h-1">
                      <div className={`h-1 rounded-full ${
                        item.status === "mastered" ? "bg-emerald-500" :
                        item.status === "needs_review" ? "bg-orange-500" : "bg-indigo-500"
                      }`} style={{ width: `${item.mastery}%` }} />
                    </div>
                  )}
                </div>
              </motion.div>
            );

            return isClickable && concept ? (
              <Link key={item.id} to={`/app/concepts/${item.conceptId}`}>{CardContent}</Link>
            ) : (
              <div key={item.id}>{CardContent}</div>
            );
          })}
        </div>
      </div>

      <div className="mt-8 p-5 bg-white/3 border border-white/6 rounded-2xl text-center">
        <p className="text-slate-400 text-sm">
          Your learning path updates automatically after each quiz based on your mastery scores.
        </p>
        <Link to="/app/quizzes" className="inline-flex items-center gap-1.5 text-indigo-400 text-sm mt-3 hover:text-indigo-300 transition-colors">
          Take a Quiz to Update Path <ChevronRight size={13} />
        </Link>
      </div>
    </div>
  );
}
