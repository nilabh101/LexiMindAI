import { useParams, Link } from "react-router-dom";
import { motion } from "framer-motion";
import { ChevronRight, Clock, BookOpen, Layers, ArrowLeft } from "lucide-react";
import { getSubject, getChaptersBySubject, getConceptsByChapter } from "../../data/curriculum";

const TABS = ["Overview", "Chapters", "Notes", "PYQs", "Quizzes"] as const;
type Tab = typeof TABS[number];

export function SubjectDetailPage() {
  const { subjectId } = useParams<{ subjectId: string }>();
  const subject = getSubject(subjectId ?? "");
  const [tab, setTab] = [("Chapters" as Tab), (v: Tab) => {}]; // simplified — no useState needed for static

  if (!subject) return (
    <div className="p-8 text-center">
      <p className="text-slate-400">Subject not found.</p>
      <Link to="/app/subjects" className="text-indigo-400 text-sm mt-2 inline-flex items-center gap-1"><ArrowLeft size={13} /> Back to Subjects</Link>
    </div>
  );

  const chapters = getChaptersBySubject(subject.id);
  const totalMinutes = chapters.reduce((s, c) => s + c.estimatedMinutes, 0);
  const totalConcepts = chapters.reduce((s, c) => s + c.conceptIds.length, 0);

  return (
    <div className="p-6 lg:p-8 max-w-5xl mx-auto">
      {/* Back */}
      <Link to="/app/subjects" className="inline-flex items-center gap-1.5 text-slate-400 hover:text-white text-sm mb-6 transition-colors">
        <ArrowLeft size={14} /> Back to Subjects
      </Link>

      {/* Subject header */}
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}
        className="bg-gradient-to-br from-indigo-600/15 to-purple-600/10 border border-indigo-500/15 rounded-3xl p-8 mb-8">
        <div className="flex items-start gap-5">
          <div className="w-16 h-16 rounded-2xl bg-indigo-600/30 flex items-center justify-center text-3xl shrink-0">
            {subject.icon}
          </div>
          <div className="flex-1">
            <h1 className="text-2xl font-bold text-white">{subject.name}</h1>
            {subject.semester && <p className="text-slate-400 text-sm mt-0.5">Semester {subject.semester}</p>}
            <p className="text-slate-400 text-sm mt-3 max-w-2xl">{subject.description}</p>
            <div className="flex flex-wrap gap-5 mt-5 text-sm text-slate-400">
              <span className="flex items-center gap-1.5"><BookOpen size={14} /> {chapters.length} Chapters</span>
              <span className="flex items-center gap-1.5"><Layers size={14} /> {totalConcepts} Concepts</span>
              <span className="flex items-center gap-1.5"><Clock size={14} /> {totalMinutes} min est.</span>
            </div>
          </div>
          {/* Overall mastery */}
          <div className="text-center shrink-0">
            <div className="text-3xl font-black text-amber-400">55%</div>
            <div className="text-xs text-slate-500 mt-1">Mastery</div>
          </div>
        </div>
      </motion.div>

      {/* Tabs */}
      <div className="flex gap-1 mb-6 border-b border-white/6">
        {TABS.map(t => (
          <button key={t}
            className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-all ${t === "Chapters" ? "border-indigo-500 text-indigo-300" : "border-transparent text-slate-400 hover:text-slate-200"}`}>
            {t}
          </button>
        ))}
      </div>

      {/* Chapters list */}
      <div className="space-y-3">
        {chapters.length === 0 ? (
          <div className="text-center py-10 text-slate-500 text-sm">No chapters available yet.</div>
        ) : chapters.map((ch, i) => {
          const concepts = getConceptsByChapter(ch.id);
          return (
            <motion.div key={ch.id} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.05 }}>
              <Link to={`/app/chapters/${ch.id}`}>
                <div className="bg-white/3 border border-white/6 rounded-2xl p-5 hover:bg-white/5 hover:border-white/10 transition-all group flex items-center gap-4">
                  <div className="w-10 h-10 rounded-xl bg-white/5 text-slate-400 flex items-center justify-center text-sm font-bold shrink-0 group-hover:bg-indigo-600/20 group-hover:text-indigo-300 transition-all">
                    {ch.order}
                  </div>
                  <div className="flex-1">
                    <div className="font-semibold text-white group-hover:text-indigo-300 transition-colors">{ch.name}</div>
                    {ch.description && <p className="text-xs text-slate-500 mt-0.5 line-clamp-1">{ch.description}</p>}
                    <div className="flex gap-4 mt-2 text-xs text-slate-500">
                      <span>{concepts.length} concepts</span>
                      <span><Clock size={10} className="inline mr-0.5" />{ch.estimatedMinutes} min</span>
                    </div>
                  </div>
                  {/* Progress */}
                  <div className="text-right shrink-0">
                    <div className="text-sm font-semibold text-amber-400">60%</div>
                    <div className="text-xs text-slate-500">progress</div>
                  </div>
                  <ChevronRight size={16} className="text-slate-600 group-hover:text-indigo-400 transition-colors shrink-0" />
                </div>
              </Link>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}
