import { useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { GitCompare, Plus, X } from "lucide-react";
import {
  RadarChart, Radar, PolarGrid, PolarAngleAxis, ResponsiveContainer,
  BarChart, Bar, XAxis, YAxis, Tooltip, Cell, Legend
} from "recharts";
import { compareDocuments, listDocuments } from "../lib/api";
import { LoadingSpinner } from "../components/LoadingSpinner";
import { PageHeader } from "../components/PageHeader";
import toast from "react-hot-toast";

const COLORS = ["#6366f1", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6"];

export function ComparePage() {
  const [selectedIds, setSelectedIds] = useState<number[]>([]);

  const { data: docs } = useQuery({
    queryKey: ["documents"],
    queryFn: () => listDocuments().then(r => r.data),
  });

  const mutation = useMutation({
    mutationFn: (ids: number[]) => compareDocuments(ids).then(r => r.data),
    onError: (e: any) => toast.error(e.message),
  });

  const docList: any[] = docs || [];
  const addDoc = (id: number) => {
    if (!selectedIds.includes(id) && selectedIds.length < 5) {
      setSelectedIds(prev => [...prev, id]);
    }
  };

  return (
    <div className="p-8">
      <PageHeader
        title="Document Comparison"
        subtitle="Compare vocabulary, sentiment, style, and DNA across documents"
        icon={<GitCompare size={22} />}
      />

      <div className="glass-card p-6 mb-6">
        <h3 className="section-title">Select Documents to Compare</h3>
        <div className="flex flex-wrap gap-2 mb-4">
          {selectedIds.map(id => {
            const doc = docList.find(d => d.id === id);
            return (
              <div key={id} className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-brand-600/30 border border-brand-500/30 text-sm text-brand-300">
                {doc?.original_filename || `Doc ${id}`}
                <button onClick={() => setSelectedIds(prev => prev.filter(x => x !== id))}>
                  <X size={12} />
                </button>
              </div>
            );
          })}
          {selectedIds.length < 5 && (
            <select
              className="input-field text-sm w-56"
              value=""
              onChange={e => e.target.value && addDoc(Number(e.target.value))}
            >
              <option value="">+ Add document…</option>
              {docList.filter(d => !selectedIds.includes(d.id)).map((d: any) => (
                <option key={d.id} value={d.id}>{d.original_filename}</option>
              ))}
            </select>
          )}
        </div>
        <button
          onClick={() => mutation.mutate(selectedIds)}
          disabled={selectedIds.length < 2 || mutation.isPending}
          className="btn-primary disabled:opacity-40 flex items-center gap-2"
        >
          <GitCompare size={16} />
          {mutation.isPending ? "Comparing…" : "Compare Documents"}
        </button>
      </div>

      {mutation.isPending && <LoadingSpinner text="Comparing documents…" />}

      {mutation.data && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
          {/* Summary */}
          <div className="glass-card p-6 mb-6 bg-gradient-to-r from-brand-500/10 to-purple-500/10 border border-brand-500/20">
            <p className="text-slate-300">{mutation.data.summary}</p>
            <div className="flex gap-6 mt-3">
              <div>
                <span className="text-2xl font-bold text-brand-400">{mutation.data.average_similarity}%</span>
                <div className="text-xs text-slate-400">Average Similarity</div>
              </div>
              <div>
                <span className="text-2xl font-bold text-emerald-400">{mutation.data.vocabulary_overlap_pct}%</span>
                <div className="text-xs text-slate-400">Vocabulary Overlap</div>
              </div>
              <div>
                <span className="text-2xl font-bold text-purple-400">{mutation.data.common_vocabulary_size}</span>
                <div className="text-xs text-slate-400">Common Words</div>
              </div>
            </div>
          </div>

          {/* Similarity matrix */}
          <div className="glass-card p-6 mb-6">
            <h3 className="section-title">Similarity Matrix</h3>
            <div className="overflow-x-auto">
              <table className="text-sm">
                <thead>
                  <tr>
                    <th className="p-3 text-slate-400"></th>
                    {mutation.data.documents.map((d: any) => (
                      <th key={d.id} className="p-3 text-slate-300 font-medium text-left max-w-32 truncate">{d.filename}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {mutation.data.documents.map((row: any, i: number) => (
                    <tr key={row.id}>
                      <td className="p-3 text-slate-300 font-medium">{row.filename}</td>
                      {mutation.data.similarity_matrix[i].map((val: number, j: number) => (
                        <td key={j} className="p-3 text-center">
                          <span className={`px-3 py-1 rounded-lg text-sm font-medium ${
                            i === j ? "bg-white/10 text-slate-400" :
                            val > 70 ? "bg-emerald-500/20 text-emerald-400" :
                            val > 40 ? "bg-amber-500/20 text-amber-400" :
                            "bg-red-500/20 text-red-400"
                          }`}>{val}%</span>
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Stat comparison bar charts */}
          <div className="glass-card p-6 mb-6">
            <h3 className="section-title">Statistics Comparison</h3>
            <div className="grid grid-cols-2 gap-4">
              {(mutation.data.stat_comparison || []).slice(0, 4).map((stat: any, i: number) => (
                <div key={i}>
                  <h4 className="text-xs text-slate-400 mb-2">{stat.metric}</h4>
                  <ResponsiveContainer width="100%" height={120}>
                    <BarChart data={stat.values}>
                      <XAxis dataKey="document" tick={{ fill: "#94a3b8", fontSize: 9 }} />
                      <YAxis tick={{ fill: "#94a3b8", fontSize: 9 }} />
                      <Tooltip contentStyle={{ background: "#1a1a2e", border: "1px solid #2d2d4a", borderRadius: 8 }} />
                      <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                        {stat.values.map((_: any, j: number) => <Cell key={j} fill={COLORS[j % COLORS.length]} />)}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              ))}
            </div>
          </div>

          {/* DNA heatmap as styled table */}
          <div className="glass-card p-6 mb-6">
            <h3 className="section-title">DNA Heatmap</h3>
            <div className="overflow-x-auto">
              <table className="text-sm w-full">
                <thead>
                  <tr>
                    <th className="p-2 text-left text-slate-400">Dimension</th>
                    {mutation.data.documents.map((d: any) => (
                      <th key={d.id} className="p-2 text-center text-slate-300">{d.filename}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {(mutation.data.dna_heatmap || []).map((row: any, i: number) => {
                    const vals = mutation.data.documents.map((d: any) => row[d.filename] || 0);
                    const max = Math.max(...vals);
                    return (
                      <tr key={i} className="border-b border-white/5">
                        <td className="p-2 text-slate-300">{row.dimension}</td>
                        {mutation.data.documents.map((d: any, j: number) => {
                          const val = row[d.filename] || 0;
                          const intensity = max > 0 ? val / max : 0;
                          return (
                            <td key={j} className="p-2 text-center">
                              <span className="px-2 py-1 rounded text-xs font-medium"
                                style={{ background: `rgba(99,102,241,${intensity * 0.6})`, color: intensity > 0.5 ? "white" : "#94a3b8" }}>
                                {val}%
                              </span>
                            </td>
                          );
                        })}
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          {/* Sentiment comparison */}
          <div className="glass-card p-6">
            <h3 className="section-title">Sentiment Comparison</h3>
            <div className="space-y-3">
              {(mutation.data.sentiment_comparison || []).map((s: any, i: number) => (
                <div key={i} className="flex items-center gap-4 p-3 rounded-xl bg-white/5">
                  <span className="font-medium text-white text-sm w-40 truncate">{s.document}</span>
                  <span className={`text-xs px-2 py-0.5 rounded-full ${
                    s.label === "positive" ? "bg-emerald-500/20 text-emerald-400" :
                    s.label === "negative" ? "bg-red-500/20 text-red-400" :
                    "bg-slate-500/20 text-slate-400"
                  }`}>{s.label}</span>
                  <div className="flex-1 text-xs text-slate-400">Polarity: {s.polarity?.toFixed(3)}</div>
                  <div className="text-xs text-slate-400">Subjectivity: {s.subjectivity?.toFixed(3)}</div>
                </div>
              ))}
            </div>
          </div>
        </motion.div>
      )}
    </div>
  );
}
