import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { FileText, Brain, BarChart3, TrendingUp, Upload, Zap, ArrowRight } from "lucide-react";
import { Link } from "react-router-dom";
import { listDocuments } from "../lib/api";
import { formatBytes, formatDate, formatNumber } from "../lib/utils";
import { KpiCard } from "../components/KpiCard";

export function Dashboard() {
  const { data, isLoading } = useQuery({
    queryKey: ["documents"],
    queryFn: () => listDocuments().then((r) => r.data),
  });

  const docs: any[] = data || [];
  const totalWords = docs.reduce((s, d) => s + (d.word_count || 0), 0);
  const totalDocs = docs.length;

  const features = [
    { icon: BarChart3, title: "Word Analysis", desc: "Frequency, TF-IDF, word clouds", to: "/words", color: "from-brand-500 to-blue-500" },
    { icon: MessageSquare, title: "Sentiment", desc: "Emotion & sentiment scoring", to: "/sentiment", color: "from-emerald-500 to-teal-500" },
    { icon: Brain, title: "Document DNA", desc: "Unique document fingerprint", to: "/dna", color: "from-purple-500 to-pink-500" },
    { icon: Zap, title: "Quiz Generator", desc: "AI-generated MCQs & questions", to: "/quiz", color: "from-amber-500 to-orange-500" },
  ];

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
            Upload documents to unlock deep linguistic analysis, sentiment detection, topic modeling,
            AI-generated summaries, quizzes, and comprehensive PDF reports.
          </p>
          <Link to="/upload" className="btn-primary inline-flex items-center gap-2 mt-6">
            <Upload size={16} />
            Upload Document
            <ArrowRight size={14} />
          </Link>
        </div>
      </motion.div>

      {/* KPIs */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <KpiCard label="Documents" value={totalDocs} icon={<FileText size={18} />} color="brand" delay={0.05} />
        <KpiCard label="Total Words" value={formatNumber(totalWords)} icon={<BarChart3 size={18} />} color="blue" delay={0.1} />
        <KpiCard label="AI Modules" value="20+" icon={<Brain size={18} />} color="purple" delay={0.15} />
        <KpiCard label="NLP Pipeline" value="Active" icon={<Zap size={18} />} sub="spaCy + TextBlob" color="green" delay={0.2} />
      </div>

      {/* Feature grid */}
      <h2 className="section-title">
        <Zap size={18} className="text-brand-400" />
        Analysis Modules
      </h2>
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {features.map(({ icon: Icon, title, desc, to, color }, i) => (
          <motion.div
            key={to}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.07 }}
          >
            <Link to={to} className="glass-card p-5 block hover:bg-white/8 transition-all hover:-translate-y-0.5 group">
              <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${color} flex items-center justify-center mb-3`}>
                <Icon size={18} className="text-white" />
              </div>
              <div className="font-semibold text-white text-sm">{title}</div>
              <div className="text-xs text-slate-400 mt-1">{desc}</div>
              <div className="flex items-center gap-1 text-xs text-brand-400 mt-3 opacity-0 group-hover:opacity-100 transition-opacity">
                Open <ArrowRight size={12} />
              </div>
            </Link>
          </motion.div>
        ))}
      </div>

      {/* Recent Documents */}
      {docs.length > 0 && (
        <>
          <h2 className="section-title">
            <FileText size={18} className="text-brand-400" />
            Recent Documents
          </h2>
          <div className="glass-card overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-white/10">
                  <th className="text-left p-4 text-slate-400 font-medium">Filename</th>
                  <th className="text-right p-4 text-slate-400 font-medium">Words</th>
                  <th className="text-right p-4 text-slate-400 font-medium">Size</th>
                  <th className="text-right p-4 text-slate-400 font-medium">Uploaded</th>
                  <th className="text-right p-4 text-slate-400 font-medium">Action</th>
                </tr>
              </thead>
              <tbody>
                {docs.slice(0, 8).map((d: any, i: number) => (
                  <motion.tr
                    key={d.id}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: i * 0.05 }}
                    className="border-b border-white/5 hover:bg-white/5 transition-colors"
                  >
                    <td className="p-4 text-white font-medium">{d.original_filename}</td>
                    <td className="p-4 text-right text-brand-300">{formatNumber(d.word_count)}</td>
                    <td className="p-4 text-right text-slate-400">{formatBytes(d.file_size)}</td>
                    <td className="p-4 text-right text-slate-500 text-xs">{formatDate(d.upload_date)}</td>
                    <td className="p-4 text-right">
                      <Link to={`/words?doc=${d.id}`} className="text-brand-400 hover:text-brand-300 text-xs">
                        Analyze →
                      </Link>
                    </td>
                  </motion.tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}

      {docs.length === 0 && !isLoading && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="glass-card p-12 text-center">
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

// Fix missing import
function MessageSquare({ size, className }: { size?: number; className?: string }) {
  return (
    <svg width={size || 24} height={size || 24} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} className={className}>
      <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
    </svg>
  );
}
