import { useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { TrendingUp, X } from "lucide-react";
import {
  LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend, CartesianGrid
} from "recharts";
import { getTrends, listDocuments } from "../lib/api";
import { LoadingSpinner } from "../components/LoadingSpinner";
import { PageHeader } from "../components/PageHeader";
import toast from "react-hot-toast";

const COLORS = ["#6366f1", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#06b6d4", "#ec4899", "#f97316"];

export function TrendsPage() {
  const [selectedIds, setSelectedIds] = useState<number[]>([]);

  const { data: docs } = useQuery({
    queryKey: ["documents"],
    queryFn: () => listDocuments().then(r => r.data),
  });

  const mutation = useMutation({
    mutationFn: (ids: number[]) => getTrends(ids).then(r => r.data),
    onError: (e: any) => toast.error(e.message),
  });

  const docList: any[] = docs || [];
  const addDoc = (id: number) => {
    if (!selectedIds.includes(id)) setSelectedIds(prev => [...prev, id]);
  };

  return (
    <div className="p-8">
      <PageHeader
        title="Trend Analysis"
        subtitle="Track keyword, topic, and sentiment evolution across documents"
        icon={<TrendingUp size={22} />}
      />

      <div className="glass-card p-6 mb-6">
        <h3 className="section-title">Select Documents</h3>
        <div className="flex flex-wrap gap-2 mb-4">
          {selectedIds.map(id => {
            const doc = docList.find(d => d.id === id);
            return (
              <div key={id} className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-brand-600/30 border border-brand-500/30 text-sm text-brand-300">
                {doc?.original_filename || `Doc ${id}`}
                <button onClick={() => setSelectedIds(prev => prev.filter(x => x !== id))}><X size={12} /></button>
              </div>
            );
          })}
          <select className="input-field text-sm w-56" value="" onChange={e => e.target.value && addDoc(Number(e.target.value))}>
            <option value="">+ Add document…</option>
            {docList.filter(d => !selectedIds.includes(d.id)).map((d: any) => (
              <option key={d.id} value={d.id}>{d.original_filename}</option>
            ))}
          </select>
        </div>
        <button
          onClick={() => mutation.mutate(selectedIds)}
          disabled={selectedIds.length < 2 || mutation.isPending}
          className="btn-primary disabled:opacity-40"
        >
          {mutation.isPending ? "Analyzing…" : "Analyze Trends"}
        </button>
      </div>

      {mutation.isPending && <LoadingSpinner text="Analyzing trends…" />}

      {mutation.data && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
          {/* Sentiment trend */}
          <div className="glass-card p-6 mb-6">
            <h3 className="section-title">Sentiment Evolution</h3>
            <ResponsiveContainer width="100%" height={280}>
              <LineChart data={mutation.data.sentiment_trends || []}>
                <CartesianGrid strokeDasharray="3 3" stroke="#2d2d4a" />
                <XAxis dataKey="document" tick={{ fill: "#94a3b8", fontSize: 10 }} />
                <YAxis domain={[-1, 1]} tick={{ fill: "#94a3b8", fontSize: 10 }} />
                <Tooltip contentStyle={{ background: "#1a1a2e", border: "1px solid #2d2d4a", borderRadius: 8 }} />
                <Legend />
                <Line type="monotone" dataKey="polarity" stroke="#6366f1" strokeWidth={2} dot name="Polarity" />
                <Line type="monotone" dataKey="subjectivity" stroke="#10b981" strokeWidth={2} dot name="Subjectivity" />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Keyword trends */}
          <div className="glass-card p-6 mb-6">
            <h3 className="section-title">Keyword Frequency Trends</h3>
            <ResponsiveContainer width="100%" height={280}>
              <LineChart data={mutation.data.keyword_trends || []}>
                <CartesianGrid strokeDasharray="3 3" stroke="#2d2d4a" />
                <XAxis dataKey="document" tick={{ fill: "#94a3b8", fontSize: 10 }} />
                <YAxis tick={{ fill: "#94a3b8", fontSize: 10 }} />
                <Tooltip contentStyle={{ background: "#1a1a2e", border: "1px solid #2d2d4a", borderRadius: 8 }} />
                <Legend />
                {(mutation.data.top_keywords || []).slice(0, 5).map((kw: string, i: number) => (
                  <Line key={kw} type="monotone" dataKey={kw} stroke={COLORS[i]} strokeWidth={2} dot name={kw} />
                ))}
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Topic trends */}
          <div className="glass-card p-6">
            <h3 className="section-title">Topic Score Trends</h3>
            <ResponsiveContainer width="100%" height={280}>
              <LineChart data={mutation.data.topic_trends || []}>
                <CartesianGrid strokeDasharray="3 3" stroke="#2d2d4a" />
                <XAxis dataKey="document" tick={{ fill: "#94a3b8", fontSize: 10 }} />
                <YAxis tick={{ fill: "#94a3b8", fontSize: 10 }} />
                <Tooltip contentStyle={{ background: "#1a1a2e", border: "1px solid #2d2d4a", borderRadius: 8 }} />
                <Legend />
                {["Technology", "Politics", "Education", "Climate", "Finance"].map((t, i) => (
                  <Line key={t} type="monotone" dataKey={t} stroke={COLORS[i]} strokeWidth={2} dot name={t} />
                ))}
              </LineChart>
            </ResponsiveContainer>
          </div>
        </motion.div>
      )}
    </div>
  );
}
