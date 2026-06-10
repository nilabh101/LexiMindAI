import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { FileText, Brain, BarChart3, Upload, Zap, ArrowRight, Search, Layers, Cpu } from "lucide-react";
import { Link } from "react-router-dom";
import { listDocuments } from "../lib/api";
import { formatBytes, formatDate, formatNumber } from "../lib/utils";

function StatCard({ label, value, sub, color }: { label: string; value: string | number; sub?: string; color: string }) {
  return (
    <div className="glass-card p-5">
      <div className={`text-2xl font-bold ${color}`}>{value}</div>
      {sub && <div className="text-xs text-slate-500 mt-0.5">{sub}</div>}
      <div className="text-xs text-slate-400 mt-1">{label}</div>
    </div>
  );
}

const FEATURES = [
  { icon: BarChart3, title: "Analysis",          desc: "Words, sentiment & AI summary",         to: "/analysis",  color: "from-brand-500 to-blue-500"    },
  { icon: Search,    title: "Search Document",   desc: "Find any word — every location",        to: "/search",    color: "from-emerald-500 to-teal-500"  },
  { icon: Zap,       title: "Quiz & Study",      desc: "MCQs, flashcards, grading, practice",   to: "/quiz",      color: "from-amber-500 to-orange-500"  },
  { icon: Layers,    title: "Topics & Entities", desc: "AI topic detection + NER",              to: "/topics",    color: "from-purple-500 to-pink-500"   },
  { icon: Brain,     title: "Document DNA",      desc: "Linguistic fingerprint radar",          to: "/dna",       color: "from-blue-500 to-cyan-500"     },
  { icon: Cpu,       title: "Core of Project",   desc: "Tech stack, modules & evolution",       to: "/core",      color: "from-slate-500 to-slate-600"   },
];

export function Dashboard() {
  const { data, isLoading } = useQuery({
    queryKey: ["documents"],
    queryFn: () => listDocuments().then((r) => r.data),
  });

  const docs: any[] = data || [];
  const totalWords     = docs.reduce((s, d) => s + (d.word_count     || 0), 0);
  const totalSentences = docs.reduce((s, d) => s + (d.sentence_count || 0), 0);

  return (
    <div className="p-8">

      {/* Hero */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="glass-card p-8 mb-8 relative overflow-hidden"
      >
        <div className="absolute inset-0 bg-gradient-to-br from-brand-500/10 via-purple-500/5 to-transparent" />
        <div className="relative">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-brand-500 to-purple-500 flex items-center justify-center shadow-lg shadow-brand-500/30">
              <Brain size={24} className="text-white" />
            </div>
            <div>
              <h1 className="text-3xl font-bold gradient-text">LexiMind AI</h1>
              <p className="text-slate-400 text-sm">Transforming Documents into Actionable Intelligence</p>
            </div>
          </div>
          <p className="text-slate-300 max-w-2xl mt-4">
            Upload documents up to <span className="text-brand-300 font-semibold">500 MB</span> and
            unlock deep text analysis — word statistics, sentiment, topic detection, in-document search,
            AI-generated quizzes and flashcards.
          </p>
          <Link to="/upload" className="btn-primary inline-flex items-center gap-2 mt-5">
            <Upload size={15} /> Upload Document <ArrowRight size={13} />
          </Link>
        </div>
      </motion.div>

      {/* KPIs */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <StatCard label="Documents"      value={docs.length}              color="text-brand-400"   />
        <StatCard label="Total Words"    value={formatNumber(totalWords)} color="text-blue-400"    />
        <StatCard label="Total Sentences"value={formatNumber(totalSentences)} color="text-purple-400" />
        <StatCard label="Max File Size"  value="500 MB" sub="per file"   color="text-emerald-400" />
      </div>

      {/* Feature grid */}
      <h2 className="section-title mb-4">
        <Zap size={17} className="text-brand-400" /> Analysis Modules
      </h2>
      <div className="grid grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
        {FEATURES.map(({ icon: Icon, title, desc, to, color }, i) => (
          <motion.div
            key={to}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.06 }}
          >
            <Link to={to} className="glass-card p-5 block hover:bg-white/8 transition-all hover:-translate-y-0.5 group">
              <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${color} flex items-center justify-center mb-3`}>
                <Icon size={17} className="text-white" />
              </div>
              <div className="font-semibold text-white text-sm">{title}</div>
              <div className="text-xs text-slate-400 mt-1">{desc}</div>
              <div className="flex items-center gap-1 text-xs text-brand-400 mt-3 opacity-0 group-hover:opacity-100 transition-opacity">
                Open <ArrowRight size={11} />
              </div>
            </Link>
          </motion.div>
        ))}
      </div>

      {/* Recent Documents */}
      {docs.length > 0 && (
        <>
          <h2 className="section-title mb-4">
            <FileText size={17} className="text-brand-400" /> Recent Documents
          </h2>
          <div className="glass-card overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-white/10">
                  <th className="text-left p-4 text-slate-400 font-medium">Filename</th>
                  <th className="text-right p-4 text-slate-400 font-medium">Words</th>
                  <th className="text-right p-4 text-slate-400 font-medium">Sentences</th>
                  <th className="text-right p-4 text-slate-400 font-medium">Size</th>
                  <th className="text-right p-4 text-slate-400 font-medium">Uploaded</th>
                  <th className="text-right p-4 text-slate-400 font-medium">Actions</th>
                </tr>
              </thead>
              <tbody>
                {docs.slice(0, 10).map((d: any, i: number) => (
                  <motion.tr
                    key={d.id}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: i * 0.04 }}
                    className="border-b border-white/5 hover:bg-white/5 transition-colors"
                  >
                    <td className="p-4 text-white font-medium max-w-xs truncate">
                      {d.original_filename || d.filename}
                    </td>
                    <td className="p-4 text-right text-brand-300">{formatNumber(d.word_count)}</td>
                    <td className="p-4 text-right text-purple-300">{formatNumber(d.sentence_count)}</td>
                    <td className="p-4 text-right text-slate-400">{formatBytes(d.file_size)}</td>
                    <td className="p-4 text-right text-slate-500 text-xs">{formatDate(d.upload_date)}</td>
                    <td className="p-4 text-right">
                      <div className="flex items-center justify-end gap-3">
                        <Link to={`/analysis`} state={{ docId: d.id }} className="text-brand-400 hover:text-brand-300 text-xs">Analyse →</Link>
                        <Link to={`/search?doc=${d.id}`}               className="text-emerald-400 hover:text-emerald-300 text-xs">Search →</Link>
                        <Link to={`/quiz?doc=${d.id}`}                 className="text-amber-400 hover:text-amber-300 text-xs">Quiz →</Link>
                      </div>
                    </td>
                  </motion.tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}

      {docs.length === 0 && !isLoading && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="glass-card p-14 text-center">
          <Upload size={40} className="text-slate-600 mx-auto mb-4" />
          <p className="text-slate-400">No documents yet. Upload your first document to get started.</p>
          <Link to="/upload" className="btn-primary inline-flex items-center gap-2 mt-4">
            <Upload size={14} /> Upload Document
          </Link>
        </motion.div>
      )}
    </div>
  );
}
