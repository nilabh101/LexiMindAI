import { useState } from "react";
import { motion } from "framer-motion";
import { FileText, Filter, ChevronDown, ChevronUp, Bookmark } from "lucide-react";
import { DEMO_PYQS } from "../../data/demoData";
import { SUBJECTS } from "../../data/curriculum";

export function PYQsPage() {
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [filterSubject, setFilterSubject] = useState("all");
  const [filterYear, setFilterYear] = useState("all");
  const [filterDifficulty, setFilterDifficulty] = useState("all");

  const years = [...new Set(DEMO_PYQS.map(q => q.year))].sort((a, b) => b - a);

  const filtered = DEMO_PYQS.filter(q => {
    if (filterSubject !== "all" && q.subjectId !== filterSubject) return false;
    if (filterYear !== "all" && String(q.year) !== filterYear) return false;
    if (filterDifficulty !== "all" && q.difficulty !== filterDifficulty) return false;
    return true;
  });

  return (
    <div className="p-6 lg:p-8 max-w-4xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white">Previous Year Questions</h1>
        <p className="text-slate-400 text-sm mt-1">Practice with real exam questions filtered by subject, year, and difficulty.</p>
      </div>

      {/* Filters */}
      <div className="bg-white/3 border border-white/6 rounded-2xl p-4 mb-6 flex flex-wrap gap-3 items-center">
        <Filter size={15} className="text-slate-400" />
        <select value={filterSubject} onChange={e => setFilterSubject(e.target.value)}
          className="bg-white/5 border border-white/10 rounded-xl px-3 py-2 text-sm text-slate-300 outline-none focus:border-indigo-500/50 transition-all">
          <option value="all">All Subjects</option>
          {SUBJECTS.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
        </select>
        <select value={filterYear} onChange={e => setFilterYear(e.target.value)}
          className="bg-white/5 border border-white/10 rounded-xl px-3 py-2 text-sm text-slate-300 outline-none focus:border-indigo-500/50 transition-all">
          <option value="all">All Years</option>
          {years.map(y => <option key={y} value={String(y)}>{y}</option>)}
        </select>
        <select value={filterDifficulty} onChange={e => setFilterDifficulty(e.target.value)}
          className="bg-white/5 border border-white/10 rounded-xl px-3 py-2 text-sm text-slate-300 outline-none focus:border-indigo-500/50 transition-all">
          <option value="all">All Difficulties</option>
          <option value="easy">Easy</option>
          <option value="medium">Medium</option>
          <option value="hard">Hard</option>
        </select>
        <span className="text-xs text-slate-500 ml-auto">{filtered.length} questions</span>
      </div>

      {/* Questions */}
      {filtered.length === 0 ? (
        <div className="bg-white/3 border border-white/6 rounded-2xl p-14 text-center">
          <FileText size={36} className="text-slate-600 mx-auto mb-3" />
          <p className="text-slate-400">No questions match the current filters.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {filtered.map((pyq, i) => {
            const sub = SUBJECTS.find(s => s.id === pyq.subjectId);
            const expanded = expandedId === pyq.id;
            return (
              <motion.div key={pyq.id} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.04 }}
                className="bg-white/3 border border-white/6 rounded-2xl overflow-hidden">
                <div className="p-5">
                  <div className="flex items-start justify-between gap-3 mb-3">
                    <div className="flex flex-wrap gap-2">
                      <span className="text-xs bg-indigo-500/15 text-indigo-300 border border-indigo-500/20 px-2 py-0.5 rounded-lg">{pyq.year}</span>
                      <span className="text-xs bg-white/8 text-slate-400 px-2 py-0.5 rounded-lg">{pyq.marks} marks</span>
                      <span className={`text-xs px-2 py-0.5 rounded-lg ${
                        pyq.difficulty === "easy" ? "bg-emerald-500/15 text-emerald-300" :
                        pyq.difficulty === "hard" ? "bg-red-500/15 text-red-300" :
                        "bg-amber-500/15 text-amber-300"
                      }`}>{pyq.difficulty}</span>
                      {sub && <span className="text-xs text-slate-500">{sub.shortName ?? sub.name}</span>}
                    </div>
                    <button className="text-slate-500 hover:text-amber-400 transition-colors shrink-0">
                      <Bookmark size={15} />
                    </button>
                  </div>
                  <p className="text-slate-200 text-sm leading-relaxed">{pyq.question}</p>
                  <div className="text-xs text-slate-600 mt-2">{pyq.source}</div>
                </div>

                {/* Expandable solution */}
                <div className="border-t border-white/6">
                  <button onClick={() => setExpandedId(expanded ? null : pyq.id)}
                    className="w-full flex items-center justify-between px-5 py-3 text-xs text-slate-400 hover:text-slate-200 transition-colors">
                    <span>View Solution & Explanation</span>
                    {expanded ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
                  </button>
                  {expanded && (
                    <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: "auto", opacity: 1 }} className="overflow-hidden">
                      <div className="px-5 pb-5 space-y-3">
                        <div>
                          <div className="text-xs text-emerald-400 font-medium mb-1.5">Solution</div>
                          <div className="text-sm text-slate-300 leading-relaxed bg-black/20 p-3 rounded-xl">{pyq.solution}</div>
                        </div>
                        <div>
                          <div className="text-xs text-indigo-400 font-medium mb-1.5">Explanation</div>
                          <div className="text-sm text-slate-400 leading-relaxed">{pyq.explanation}</div>
                        </div>
                      </div>
                    </motion.div>
                  )}
                </div>
              </motion.div>
            );
          })}
        </div>
      )}
    </div>
  );
}
