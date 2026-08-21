import { useParams, Link } from "react-router-dom";
import { motion } from "framer-motion";
import { ArrowLeft, Clock, ChevronRight, CheckCircle, AlertCircle, Circle } from "lucide-react";
import { getChapter, getConceptsByChapter, getSubject } from "../../data/curriculum";
import { getMastery, masteryColor } from "../../services/adaptiveEngine";

export function ChapterPage() {
  const { chapterId } = useParams<{ chapterId: string }>();
  const chapter = getChapter(chapterId ?? "");
  const subject = chapter ? getSubject(chapter.subjectId) : null;
  const concepts = chapterId ? getConceptsByChapter(chapterId) : [];

  if (!chapter) return (
    <div className="p-8 text-center">
      <p className="text-slate-400">Chapter not found.</p>
      <Link to="/app/subjects" className="text-indigo-400 text-sm mt-2 inline-flex items-center gap-1"><ArrowLeft size={13} />Subjects</Link>
    </div>
  );

  function StatusIcon({ status }: { status: string }) {
    if (status === "mastered") return <CheckCircle size={16} className="text-emerald-400" />;
    if (status === "needs_review") return <AlertCircle size={16} className="text-amber-400" />;
    if (status === "in_progress") return <Circle size={16} className="text-indigo-400" />;
    return <Circle size={16} className="text-slate-600" />;
  }

  return (
    <div className="p-6 lg:p-8 max-w-4xl mx-auto">
      <Link to={`/app/subjects/${chapter.subjectId}`} className="inline-flex items-center gap-1.5 text-slate-400 hover:text-white text-sm mb-6 transition-colors">
        <ArrowLeft size={14} /> {subject?.name ?? "Back"}
      </Link>

      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="bg-white/3 border border-white/6 rounded-3xl p-7 mb-8">
        <div className="flex items-start justify-between">
          <div>
            <div className="text-xs text-slate-500 mb-1">Chapter {chapter.order}</div>
            <h1 className="text-2xl font-bold text-white">{chapter.name}</h1>
            {chapter.description && <p className="text-slate-400 text-sm mt-2 max-w-xl">{chapter.description}</p>}
            <div className="flex gap-5 mt-4 text-sm text-slate-500">
              <span>{concepts.length} concepts</span>
              <span className="flex items-center gap-1"><Clock size={13} />{chapter.estimatedMinutes} min</span>
            </div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-black text-amber-400">60%</div>
            <div className="text-xs text-slate-500 mt-1">Mastered</div>
          </div>
        </div>
      </motion.div>

      <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-4">Concepts</h2>
      <div className="space-y-2.5">
        {concepts.map((concept, i) => {
          const mastery = getMastery(concept.id);
          const status = mastery?.status ?? "not_started";
          const score = mastery?.score ?? 0;
          return (
            <motion.div key={concept.id} initial={{ opacity: 0, x: -8 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.05 }}>
              <Link to={`/app/concepts/${concept.id}`}>
                <div className="bg-white/3 border border-white/6 rounded-2xl p-5 hover:bg-white/5 hover:border-white/10 transition-all group flex items-center gap-4">
                  {/* Connector line */}
                  <div className="flex flex-col items-center shrink-0">
                    <StatusIcon status={status} />
                    {i < concepts.length - 1 && <div className="w-px h-8 bg-white/10 mt-1" />}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-white group-hover:text-indigo-300 transition-colors">{concept.name}</span>
                      <span className={`text-[10px] px-2 py-0.5 rounded-full capitalize ${
                        concept.difficulty === "beginner" ? "bg-emerald-500/15 text-emerald-300" :
                        concept.difficulty === "intermediate" ? "bg-amber-500/15 text-amber-300" :
                        "bg-red-500/15 text-red-300"
                      }`}>{concept.difficulty}</span>
                    </div>
                    <p className="text-xs text-slate-500 mt-0.5 line-clamp-1">{concept.description}</p>
                    <div className="flex gap-4 mt-2 text-xs text-slate-500">
                      <span><Clock size={10} className="inline mr-0.5" />{concept.estimatedMinutes} min</span>
                      {concept.prerequisites.length > 0 && <span>{concept.prerequisites.length} prerequisites</span>}
                    </div>
                  </div>
                  <div className="text-right shrink-0">
                    {score > 0 && <div className={`text-sm font-bold ${masteryColor(score)}`}>{score}%</div>}
                  </div>
                  <ChevronRight size={15} className="text-slate-600 group-hover:text-indigo-400 shrink-0" />
                </div>
              </Link>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}
