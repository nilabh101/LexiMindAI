import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { BarChart3, Search } from "lucide-react";
import { useLocation } from "react-router-dom";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, Treemap
} from "recharts";
import { getWordAnalysis, getWordCloud, getLexicalDiversity } from "../lib/api";
import { DocSelector } from "../components/DocSelector";
import { LoadingSpinner } from "../components/LoadingSpinner";
import { PageHeader } from "../components/PageHeader";

const COLORS = ["#6366f1", "#8b5cf6", "#a855f7", "#ec4899", "#06b6d4", "#10b981", "#f59e0b"];

export function WordAnalysis() {
  const location = useLocation();
  const initialDocId = location.state?.docId || null;
  const [docId, setDocId] = useState<number | null>(initialDocId);
  const [topN, setTopN] = useState(25);
  const [useStemming, setUseStemming] = useState(false);
  const [search, setSearch] = useState("");
  const [tab, setTab] = useState<"bar" | "table" | "cloud" | "treemap">("bar");

  const { data, isLoading } = useQuery({
    queryKey: ["words", docId, topN, useStemming],
    queryFn: () => getWordAnalysis(docId!, topN, useStemming).then(r => r.data),
    enabled: !!docId,
  });

  const { data: wcData, isLoading: wcLoading } = useQuery({
  queryKey: ["wordcloud", docId],
  queryFn: () => getWordCloud(docId!).then(r => r.data),
  enabled: !!docId && tab === "cloud",
});

const { data: lexicalData, isLoading: lexicalLoading } = useQuery({
  queryKey: ["lexical_diversity", docId],
  queryFn: () => getLexicalDiversity(docId!).then(r => r.data),
  enabled: !!docId,
});
  const words: any[] = data?.frequency || [];
  const filtered = words.filter(w => !search || w.word.includes(search.toLowerCase()));

  return (
    <div className="p-8">
      <PageHeader
        title="Word Analysis"
        subtitle="Frequency, TF-IDF, word clouds, and treemaps"
        icon={<BarChart3 size={22} />}
      />

      <div className="flex items-center gap-4 mb-6">
        <DocSelector value={docId} onChange={setDocId} className="flex-1 max-w-sm" />
        <select
          value={topN}
          onChange={e => setTopN(Number(e.target.value))}
          className="input-field w-32"
        >
          {[10, 25, 50, 100].map(n => <option key={n} value={n}>Top {n}</option>)}
        </select>
        <select
          value={useStemming ? "stem" : "lemma"}
          onChange={e => setUseStemming(e.target.value === "stem")}
          className="input-field w-44"
        >
          <option value="lemma">Lemmatization</option>
          <option value="stem">Stemming (Porter)</option>
        </select>
      </div>

      {!docId && (
        <div className="glass-card p-12 text-center text-slate-400">
          Select a document to begin word analysis
        </div>
      )}

      {docId && isLoading && <LoadingSpinner text="Analyzing words…" />}

      {data && (
        <>
          {/* Stats row */}
          <div className="grid grid-cols-4 gap-4 mb-6">
            <div className="glass-card p-4 text-center">
              <div className="text-2xl font-bold text-brand-400">{data.total_tokens?.toLocaleString()}</div>
              <div className="text-xs text-slate-400 mt-1">Clean Tokens</div>
            </div>
            <div className="glass-card p-4 text-center">
              <div className="text-2xl font-bold text-purple-400">{words.length}</div>
              <div className="text-xs text-slate-400 mt-1">Unique Words</div>
            </div>
            <div className="glass-card p-4 text-center">
              <div className="text-2xl font-bold text-emerald-400">{words[0]?.word || "—"}</div>
              <div className="text-xs text-slate-400 mt-1">Top Word</div>
            </div>
            <div className="glass-card p-4 text-center">
              <div className="text-2xl font-bold text-orange-400">{lexicalLoading ? '…' : lexicalData?.lexical_diversity?.toLocaleString() ?? '—'}</div>
              <div className="text-xs text-slate-400 mt-1">Lexical Diversity</div>
            </div>
          </div>

          {/* Tabs */}
          <div className="flex gap-2 mb-4">
            {(["bar", "table", "cloud", "treemap"] as const).map(t => (
              <button
                key={t}
                onClick={() => setTab(t)}
                className={`px-4 py-2 rounded-xl text-sm font-medium transition-all ${
                  tab === t ? "bg-brand-600 text-white" : "bg-white/5 text-slate-400 hover:text-white"
                }`}
              >
                {t.charAt(0).toUpperCase() + t.slice(1)}
              </button>
            ))}
          </div>

          {/* Bar Chart */}
          {tab === "bar" && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="glass-card p-6">
              <h3 className="section-title">Top {topN} Words</h3>
              <ResponsiveContainer width="100%" height={400}>
                <BarChart data={words.slice(0, topN)} margin={{ left: 0, bottom: 60 }}>
                  <XAxis dataKey="word" angle={-45} textAnchor="end" tick={{ fill: "#94a3b8", fontSize: 11 }} />
                  <YAxis tick={{ fill: "#94a3b8", fontSize: 11 }} />
                  <Tooltip
                    contentStyle={{ background: "#1a1a2e", border: "1px solid #2d2d4a", borderRadius: 8 }}
                    labelStyle={{ color: "#e2e8f0" }}
                    itemStyle={{ color: "#818cf8" }}
                  />
                  <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                    {words.slice(0, topN).map((_, i) => (
                      <Cell key={i} fill={COLORS[i % COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </motion.div>
          )}

          {/* Table */}
          {tab === "table" && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="glass-card overflow-hidden">
              <div className="p-4 border-b border-white/10 flex items-center gap-2">
                <Search size={16} className="text-slate-400" />
                <input
                  className="input-field text-sm"
                  placeholder="Search words…"
                  value={search}
                  onChange={e => setSearch(e.target.value)}
                />
              </div>
              <div className="overflow-y-auto max-h-96">
                <table className="w-full text-sm">
                  <thead className="sticky top-0 bg-surface-card">
                    <tr className="border-b border-white/10">
                      <th className="p-3 text-left text-slate-400 font-medium">Rank</th>
                      <th className="p-3 text-left text-slate-400 font-medium">Word</th>
                      <th className="p-3 text-right text-slate-400 font-medium">Count</th>
                      <th className="p-3 text-right text-slate-400 font-medium">%</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filtered.map((w: any, i: number) => (
                      <tr key={i} className="border-b border-white/5 hover:bg-white/5">
                        <td className="p-3 text-slate-500">#{w.rank}</td>
                        <td className="p-3 font-medium text-white">{w.word}</td>
                        <td className="p-3 text-right text-brand-300">{w.count}</td>
                        <td className="p-3 text-right text-slate-400">{w.percentage}%</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </motion.div>
          )}

          {/* Word Cloud */}
          {tab === "cloud" && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="glass-card p-6">
              {wcLoading && <LoadingSpinner text="Generating word cloud…" />}
              {wcData?.image_base64 && (
                <img
                  src={`data:image/png;base64,${wcData.image_base64}`}
                  alt="Word Cloud"
                  className="w-full rounded-xl"
                />
              )}
              {wcData && !wcData.image_base64 && wcData.data && (
                <div className="flex flex-wrap gap-2 justify-center p-4">
                  {wcData.data.slice(0, 80).map((w: any, i: number) => (
                    <span
                      key={i}
                      className="text-brand-300 transition-all hover:text-white"
                      style={{ fontSize: `${Math.max(0.7, Math.min(2.5, w.weight * 8))}rem` }}
                    >
                      {w.text}
                    </span>
                  ))}
                </div>
              )}
            </motion.div>
          )}

          {/* Treemap */}
          {tab === "treemap" && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="glass-card p-6">
              <h3 className="section-title">Vocabulary Treemap</h3>
              <ResponsiveContainer width="100%" height={420}>
                <Treemap
                  data={words.slice(0, 40).map(w => ({ name: w.word, size: w.count }))}
                  dataKey="size"
                  aspectRatio={4 / 3}
                  content={(({ x, y, width, height, name, value }: any) => (
                    <g>
                      <rect x={x} y={y} width={width} height={height}
                        fill={COLORS[Math.floor(Math.random() * COLORS.length)]}
                        fillOpacity={0.85} stroke="#0f0f1a" strokeWidth={2} rx={4} />
                      {width > 40 && height > 20 && (
                        <text x={x + width / 2} y={y + height / 2} textAnchor="middle"
                          dominantBaseline="middle" fill="white" fontSize={Math.min(14, width / 6)}>
                          {name}
                        </text>
                      )}
                    </g>
                  )) as any}
                />
              </ResponsiveContainer>
            </motion.div>
          )}
        </>
      )}
    </div>
  );
}
