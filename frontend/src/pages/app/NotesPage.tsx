import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { motion } from "framer-motion";
import { StickyNote, BookOpen, ChevronRight, ArrowLeft } from "lucide-react";
import { SUBJECTS } from "../../data/curriculum";
import { listAcademicNotes, getAcademicNote } from "../../lib/api";

type AcademicNoteView = {
  id: number;
  title: string;
  subjectId?: string;
  summary?: string;
  source?: string;
  isDemo?: boolean;
  keyPoints?: string[];
  formulas?: string[];
  content?: string;
};

export function NotesPage() {
  const [tab, setTab] = useState<"leximind" | "mine">("leximind");
  const [allNotes, setAllNotes] = useState<AcademicNoteView[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listAcademicNotes()
      .then(r => setAllNotes(r.data || []))
      .catch(e => setError(e?.message || "Could not load notes"));
  }, []);

  const notes = allNotes.filter(n => tab === "leximind" ? n.source !== "USER" : n.source === "USER");

  return (
    <div className="p-6 lg:p-8 max-w-4xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white">Notes</h1>
        <p className="text-slate-400 text-sm mt-1">Curated study notes and your personal uploads.</p>
      </div>

      <div className="flex gap-2 mb-6">
        {(["leximind", "mine"] as const).map(t => (
          <button key={t} onClick={() => setTab(t)}
            className={`px-5 py-2.5 rounded-xl text-sm font-medium transition-all ${tab === t ? "bg-indigo-600 text-white" : "bg-white/5 text-slate-400 hover:text-white"}`}>
            {t === "leximind" ? "LexiMind Notes" : "My Notes"}
          </button>
        ))}
      </div>

      {error && <p className="text-sm text-red-300 mb-4">{error}</p>}

      {notes.length === 0 ? (
        <div className="bg-white/3 border border-white/6 rounded-2xl p-14 text-center">
          <StickyNote size={36} className="text-slate-600 mx-auto mb-3" />
          <p className="text-slate-400">{tab === "mine" ? "You haven't uploaded any notes yet." : "No notes available yet."}</p>
          {tab === "mine" && <Link to="/app/library" className="inline-flex items-center gap-1.5 text-indigo-400 text-sm mt-3"><BookOpen size={13} /> Upload Notes</Link>}
        </div>
      ) : (
        <div className="space-y-3">
          {notes.map((note, i) => {
            const sub = SUBJECTS.find(s => s.id === note.subjectId);
            return (
              <motion.div key={note.id} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.05 }}>
                <Link to={`/app/notes/${note.id}`}>
                  <div className="bg-white/3 border border-white/6 rounded-2xl p-5 hover:bg-white/5 hover:border-white/10 transition-all group flex items-start justify-between gap-4">
                    <div className="flex items-start gap-4 flex-1 min-w-0">
                      <div className="w-10 h-10 rounded-xl bg-indigo-600/20 text-indigo-300 flex items-center justify-center shrink-0">
                        <StickyNote size={18} />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="font-semibold text-white group-hover:text-indigo-300 transition-colors truncate">{note.title}</div>
                        <div className="text-xs text-slate-500 mt-0.5">{sub?.name}</div>
                        {note.summary && <p className="text-xs text-slate-400 mt-1.5 line-clamp-2">{note.summary}</p>}
                        {note.source === "AI_GENERATED" && (
                          <div className="text-[10px] text-indigo-400 mt-1">AI-generated from your study material</div>
                        )}
                        {note.isDemo && <div className="text-[10px] text-slate-500 mt-1">DEMO</div>}
                        {note.keyPoints && note.keyPoints.length > 0 && (
                          <div className="flex flex-wrap gap-1.5 mt-2">
                            {note.keyPoints.slice(0, 3).map((kp: string, j: number) => (
                              <span key={j} className="text-[10px] bg-white/5 text-slate-400 px-2 py-0.5 rounded-lg">{kp}</span>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                    <ChevronRight size={16} className="text-slate-600 group-hover:text-indigo-400 shrink-0 mt-1 transition-colors" />
                  </div>
                </Link>
              </motion.div>
            );
          })}
        </div>
      )}
    </div>
  );
}

export function NoteDetailPage() {
  const { noteId } = useParams<{ noteId: string }>();
  const [note, setNote] = useState<AcademicNoteView | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!noteId || Number.isNaN(Number(noteId))) {
      setError("Note not found.");
      return;
    }
    getAcademicNote(Number(noteId))
      .then(r => setNote(r.data))
      .catch(e => setError(e?.message || "Note not found."));
  }, [noteId]);

  const sub = SUBJECTS.find(s => s.id === note?.subjectId);

  if (error) return <div className="p-8 text-center text-slate-400">{error}</div>;
  if (!note) return <div className="p-8 text-center text-slate-400">Loading note…</div>;

  return (
    <div className="p-6 lg:p-8 max-w-3xl mx-auto">
      <Link to="/app/notes" className="inline-flex items-center gap-1.5 text-slate-400 hover:text-white text-sm mb-6 transition-colors">
        <ArrowLeft size={14} /> Back to Notes
      </Link>
      <div className="mb-6">
        <div className="text-xs text-slate-500 mb-1">{sub?.name}</div>
        <h1 className="text-2xl font-bold text-white">{note.title}</h1>
        {note.source === "AI_GENERATED" && (
          <p className="text-xs text-indigo-400 mt-2">AI-generated from your study material</p>
        )}
        {note.isDemo && <p className="text-xs text-slate-500 mt-2">DEMO</p>}
      </div>
      {note.formulas && note.formulas.length > 0 && (
        <div className="bg-black/30 border border-white/8 rounded-2xl p-5 mb-6">
          <div className="text-xs text-emerald-400 font-medium mb-2">Key Formula</div>
          {note.formulas.map((f: string, i: number) => (
            <div key={i} className="font-mono text-emerald-300 text-sm">{f}</div>
          ))}
        </div>
      )}
      <div className="prose prose-invert prose-sm max-w-none">
        {(note.content || "").split("\n").map((line: string, i: number) => {
          if (line.startsWith("# ")) return <h1 key={i} className="text-xl font-bold text-white mt-6 mb-3">{line.slice(2)}</h1>;
          if (line.startsWith("## ")) return <h2 key={i} className="text-lg font-semibold text-white mt-5 mb-2">{line.slice(3)}</h2>;
          if (line.startsWith("**") && line.endsWith("**")) return <p key={i} className="font-semibold text-slate-200">{line.slice(2, -2)}</p>;
          if (line.startsWith("- ")) return <li key={i} className="text-slate-300 text-sm ml-4">{line.slice(2)}</li>;
          if (line.trim() === "") return <div key={i} className="h-2" />;
          return <p key={i} className="text-slate-300 text-sm leading-relaxed">{line}</p>;
        })}
      </div>
    </div>
  );
}
