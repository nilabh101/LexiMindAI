import { useParams, Link } from "react-router-dom";
import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { ArrowLeft, Clock, CheckCircle, BookOpen, Zap, MessageCircle, ChevronRight } from "lucide-react";
import { getConcept, getSubject, getChapter, CONCEPTS } from "../../data/curriculum";
import { useMasteryMap, masteryColor, masteryBgColor, statusLabel } from "../../services/adaptiveEngine";
import { listAcademicNotes, listQuestions } from "../../lib/api";

export function ConceptPage() {
  const { conceptId } = useParams<{ conceptId: string }>();
  const concept = getConcept(conceptId ?? "");
  const subject = concept ? getSubject(concept.subjectId) : null;
  const chapter = concept ? getChapter(concept.chapterId) : null;
  const { map: masteryMap } = useMasteryMap();
  const mastery = conceptId ? masteryMap[conceptId] : undefined;

  const [notes, setNotes] = useState<any[]>([]);
  const [pyqs, setPyqs] = useState<any[]>([]);

  useEffect(() => {
    if (!conceptId) return;
    listAcademicNotes({ concept_id: conceptId }).then(r => setNotes(r.data || [])).catch(() => setNotes([]));
    listQuestions({ concept_id: conceptId }).then(r => setPyqs((r.data || []).filter((q: any) => q.source === "PYQ" || q.source === "DEMO"))).catch(() => setPyqs([]));
  }, [conceptId]);
  const prereqConcepts = concept?.prerequisites.map(id => CONCEPTS.find(c => c.id === id)).filter(Boolean) ?? [];

  if (!concept) return (
    <div className="p-8 text-center">
      <p className="text-slate-400">Concept not found.</p>
      <Link to="/app/subjects" className="text-indigo-400 text-sm mt-2 inline-flex items-center gap-1"><ArrowLeft size={13} />Subjects</Link>
    </div>
  );

  return (
    <div className="p-6 lg:p-8 max-w-4xl mx-auto">
      {/* Breadcrumb */}
      <div className="flex items-center gap-1.5 text-xs text-slate-500 mb-6">
        <Link to="/app/subjects" className="hover:text-slate-300">{subject?.name}</Link>
        <ChevronRight size={12} />
        <Link to={`/app/chapters/${chapter?.id}`} className="hover:text-slate-300">{chapter?.name}</Link>
        <ChevronRight size={12} />
        <span className="text-slate-300">{concept.name}</span>
      </div>

      {/* Concept header */}
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}
        className="bg-gradient-to-br from-indigo-600/15 to-purple-600/8 border border-indigo-500/15 rounded-3xl p-7 mb-8">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              <span className={`text-xs px-2.5 py-1 rounded-full capitalize border ${
                concept.difficulty === "beginner" ? "bg-emerald-500/15 text-emerald-300 border-emerald-500/20" :
                concept.difficulty === "intermediate" ? "bg-amber-500/15 text-amber-300 border-amber-500/20" :
                "bg-red-500/15 text-red-300 border-red-500/20"
              }`}>{concept.difficulty}</span>
              {mastery && (
                <span className={`text-xs px-2.5 py-1 rounded-full border ${masteryBgColor(mastery.score)}`}>
                  {statusLabel(mastery.status)}
                </span>
              )}
            </div>
            <h1 className="text-2xl font-bold text-white mb-2">{concept.name}</h1>
            <p className="text-slate-400 text-sm leading-relaxed">{concept.description}</p>
            <div className="flex gap-5 mt-4 text-sm text-slate-500">
              <span className="flex items-center gap-1"><Clock size={13} /> {concept.estimatedMinutes} min</span>
              {prereqConcepts.length > 0 && <span>{prereqConcepts.length} prerequisites</span>}
            </div>
          </div>
          {mastery && (
            <div className="text-center shrink-0">
              <div className={`text-4xl font-black ${masteryColor(mastery.score)}`}>{Math.round(mastery.score)}%</div>
              <div className="text-xs text-slate-500 mt-1">LexiMind Mastery Score</div>
              {mastery.questionsAttempted > 0 && (
                <div className="text-[10px] text-slate-500 mt-0.5">
                  {mastery.questionsCorrect}/{mastery.questionsAttempted} correct
                </div>
              )}
            </div>
          )}
        </div>

        {/* Formula */}
        {concept.formulaSummary && (
          <div className="mt-5 p-4 bg-black/30 rounded-xl border border-white/8 font-mono text-sm text-emerald-300">
            {concept.formulaSummary}
          </div>
        )}
      </motion.div>

      {/* Action buttons */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-8">
        {[
          { label: "Study Concept", icon: BookOpen, color: "bg-indigo-600 hover:bg-indigo-500 text-white", to: `/app/notes?concept=${conceptId}` },
          { label: "Practice", icon: Zap, color: "bg-amber-600/80 hover:bg-amber-600 text-white", to: `/app/quizzes?concept=${conceptId}` },
          { label: "Take Quiz", icon: CheckCircle, color: "bg-emerald-600/80 hover:bg-emerald-600 text-white", to: `/app/quizzes?concept=${conceptId}` },
          { label: "Ask Tutor", icon: MessageCircle, color: "bg-purple-600/80 hover:bg-purple-600 text-white", to: `/app/tutor?concept=${conceptId}` },
        ].map(({ label, icon: Icon, color, to }) => (
          <Link key={label} to={to}
            className={`${color} px-4 py-3 rounded-xl text-sm font-semibold flex items-center justify-center gap-2 transition-all`}>
            <Icon size={15} /> {label}
          </Link>
        ))}
      </div>

      {/* Key points */}
      {concept.keyPoints.length > 0 && (
        <div className="bg-white/3 border border-white/6 rounded-2xl p-6 mb-5">
          <h3 className="font-semibold text-white mb-4">Key Points</h3>
          <ul className="space-y-2.5">
            {concept.keyPoints.map((pt, i) => (
              <li key={i} className="flex items-start gap-3 text-sm text-slate-300">
                <span className="w-5 h-5 rounded-full bg-indigo-600/30 text-indigo-300 flex items-center justify-center text-xs shrink-0 mt-0.5">{i + 1}</span>
                {pt}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Prerequisites */}
      {prereqConcepts.length > 0 && (
        <div className="bg-white/3 border border-white/6 rounded-2xl p-6 mb-5">
          <h3 className="font-semibold text-white mb-4">Prerequisites</h3>
          <div className="flex flex-wrap gap-2">
            {prereqConcepts.map(pre => pre && (
              <Link key={pre.id} to={`/app/concepts/${pre.id}`}
                className="flex items-center gap-2 px-3 py-2 rounded-xl bg-white/5 border border-white/8 text-sm text-slate-300 hover:text-white hover:bg-white/8 transition-all">
                {pre.name} <ChevronRight size={12} />
              </Link>
            ))}
          </div>
        </div>
      )}

      {/* Notes */}
      {notes.length > 0 && (
        <div className="mb-5">
          <h3 className="font-semibold text-white mb-3">Study Notes</h3>
          <div className="space-y-2">
            {notes.map(note => (
              <Link key={note.id} to={`/app/notes/${note.id}`}>
                <div className="bg-white/3 border border-white/6 rounded-xl p-4 hover:bg-white/5 transition-all flex items-center justify-between">
                  <div>
                    <div className="text-sm font-medium text-white">{note.title}</div>
                    <div className="text-xs text-slate-500 mt-0.5">{note.summary?.slice(0, 80)}{note.isDemo ? " · DEMO" : ""}</div>
                  </div>
                  <ChevronRight size={14} className="text-slate-500 shrink-0 ml-3" />
                </div>
              </Link>
            ))}
          </div>
        </div>
      )}

      {/* PYQs */}
      {pyqs.length > 0 && (
        <div>
          <h3 className="font-semibold text-white mb-3">Previous Year Questions</h3>
          <div className="space-y-3">
            {pyqs.map(pyq => (
              <div key={pyq.id} className="bg-white/3 border border-white/6 rounded-xl p-5">
                <div className="flex items-start justify-between gap-3 mb-3">
                  <p className="text-sm text-slate-200 leading-relaxed">{pyq.question}</p>
                  <div className="shrink-0 flex gap-2">
                    {pyq.year != null && <span className="text-xs bg-indigo-500/15 text-indigo-300 px-2 py-0.5 rounded-lg">{pyq.year}</span>}
                    {pyq.marks != null && <span className="text-xs bg-white/8 text-slate-400 px-2 py-0.5 rounded-lg">{pyq.marks}M</span>}
                    {pyq.source && <span className="text-xs bg-white/8 text-slate-500 px-2 py-0.5 rounded-lg">{pyq.source}</span>}
                  </div>
                </div>
                <details className="text-xs text-slate-400">
                  <summary className="cursor-pointer text-indigo-400 hover:text-indigo-300 transition-colors">Show Solution</summary>
                  {pyq.answer && <div className="mt-2 p-3 bg-black/20 rounded-lg leading-relaxed">{pyq.answer}</div>}
                  {pyq.explanation && <div className="mt-1.5 text-slate-500">{pyq.explanation}</div>}
                </details>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
