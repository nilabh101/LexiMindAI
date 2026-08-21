import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { ArrowRight, Clock, CheckCircle } from "lucide-react";
import {
  masteryColor, pathStatusToUi, useAdaptive, currentUserId, currentSubjectId,
  fetchLearningPath, type PathItem,
} from "../../services/adaptiveEngine";
import { getConcept, getSubject } from "../../data/curriculum";
import { loadUser } from "../../store/userStore";

export function LearnPage() {
  const user = loadUser();
  const userId = currentUserId(user);
  const subjectId = currentSubjectId(user);
  const { data: path, loading } = useAdaptive<PathItem[]>(
    () => fetchLearningPath(userId, subjectId), [userId, subjectId], []);

  const available = path.filter(i => pathStatusToUi(i.status) !== "locked");
  const currentFocus = path.find(i => i.isCurrentFocus);
  const current = currentFocus ? getConcept(currentFocus.conceptId) : null;
  const currentSub = current ? getSubject(current.subjectId) : null;
  const currentMastery = currentFocus?.mastery ?? 0;

  return (
    <div className="p-6 lg:p-8 max-w-4xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white">Learn</h1>
        <p className="text-slate-400 text-sm mt-1">Continue your learning path or jump to any available concept.</p>
      </div>

      {/* Current focus */}
      {current && (
        <div className="mb-8">
          <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">Now Studying</h2>
          <Link to={`/app/concepts/${current.id}`}>
            <div className="bg-gradient-to-br from-indigo-600/20 to-purple-600/10 border border-indigo-500/20 rounded-3xl p-7 hover:border-indigo-500/40 transition-all group">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <div className="text-xs text-indigo-300 mb-2">Current Focus · {currentSub?.name}</div>
                  <h3 className="text-2xl font-bold text-white group-hover:text-indigo-300 transition-colors">{current.name}</h3>
                  <p className="text-slate-400 text-sm mt-2 max-w-xl">{current.description}</p>
                  <div className="flex gap-5 mt-4 text-sm text-slate-500">
                    <span className="flex items-center gap-1.5"><Clock size={13} />{current.estimatedMinutes} min</span>
                    <span className="capitalize">{current.difficulty}</span>
                  </div>
                </div>
                <div className="flex items-center gap-1.5 text-indigo-400 font-medium group-hover:gap-3 transition-all shrink-0">
                  Continue <ArrowRight size={16} />
                </div>
              </div>
              <div className="mt-5 bg-black/20 rounded-full h-1.5">
                <div className="bg-indigo-500 h-1.5 rounded-full" style={{ width: `${Math.max(currentMastery, 2)}%` }} />
              </div>
              <div className="text-xs text-slate-500 mt-1">{Math.round(currentMastery)}% LexiMind Mastery Score</div>
            </div>
          </Link>
        </div>
      )}

      {/* Up next */}
      <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">Up Next</h2>
      <div className="space-y-2.5">
        {available.filter(i => !i.isCurrentFocus).slice(0, 6).map((item, idx) => {
          const uiStatus = pathStatusToUi(item.status);
          const concept = getConcept(item.conceptId);
          const sub = concept ? getSubject(concept.subjectId) : null;
          if (!concept) return null;
          return (
            <motion.div key={item.id} initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: idx * 0.05 }}>
              <Link to={`/app/concepts/${concept.id}`}>
                <div className="bg-white/3 border border-white/6 rounded-2xl p-5 hover:bg-white/5 transition-all group flex items-center gap-4">
                  <div className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 ${uiStatus === "mastered" ? "bg-emerald-500/20 text-emerald-400" : "bg-white/5 text-slate-400"}`}>
                    {uiStatus === "mastered" ? <CheckCircle size={16} /> : <span className="text-xs font-bold">{idx + 1}</span>}
                  </div>
                  <div className="flex-1">
                    <div className="text-sm font-semibold text-white group-hover:text-indigo-300 transition-colors">{concept.name}</div>
                    <div className="text-xs text-slate-500 mt-0.5">{sub?.name} · {concept.estimatedMinutes} min</div>
                  </div>
                  {item.mastery > 0 && <div className={`text-sm font-bold shrink-0 ${masteryColor(item.mastery)}`}>{Math.round(item.mastery)}%</div>}
                  <ArrowRight size={14} className="text-slate-600 group-hover:text-indigo-400 shrink-0 transition-colors" />
                </div>
              </Link>
            </motion.div>
          );
        })}
      </div>

      {available.length === 0 && !loading && (
        <div className="text-center py-10 text-slate-400">
          <p>No concepts available yet. Complete onboarding to see your learning path.</p>
          <Link to="/onboarding" className="text-indigo-400 text-sm mt-3 inline-block hover:text-indigo-300">Set up profile →</Link>
        </div>
      )}
    </div>
  );
}
