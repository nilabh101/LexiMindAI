import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { MessageSquare } from "lucide-react";
import {
  PieChart, Pie, Cell, Tooltip, ResponsiveContainer,
  RadarChart, Radar, PolarGrid, PolarAngleAxis, LineChart, Line, XAxis, YAxis
} from "recharts";
import { getSentiment, getEmotions } from "../lib/api";
import { DocSelector } from "../components/DocSelector";
import { LoadingSpinner } from "../components/LoadingSpinner";
import { PageHeader } from "../components/PageHeader";
import { KpiCard } from "../components/KpiCard";

const SENT_COLORS = { positive: "#22c55e", negative: "#ef4444", neutral: "#94a3b8", mixed: "#f59e0b" };
const EMOTION_COLORS = ["#6366f1", "#ec4899", "#f59e0b", "#ef4444", "#10b981", "#06b6d4", "#8b5cf6", "#f97316"];

export function SentimentPage() {
  const [docId, setDocId] = useState<number | null>(null);
  const [tab, setTab] = useState<"sentiment" | "emotions">("sentiment");

  const { data: sentData, isLoading: sentLoading } = useQuery({
    queryKey: ["sentiment", docId],
    queryFn: () => getSentiment(docId!).then(r => r.data),
    enabled: !!docId,
  });

  const { data: emotData, isLoading: emotLoading } = useQuery({
    queryKey: ["emotions", docId],
    queryFn: () => getEmotions(docId!).then(r => r.data),
    enabled: !!docId && tab === "emotions",
  });

  const dist = sentData?.distribution || {};
  const pieData = Object.entries(dist).map(([name, value]) => ({ name, value }));
  const trendData = sentData?.trend?.slice(0, 60) || [];

  return (
    <div className="p-8">
      <PageHeader
        title="Sentiment & Emotion Analysis"
        subtitle="Sentence-level, paragraph-level, and document-level sentiment"
        icon={<MessageSquare size={22} />}
      />

      <div className="flex items-center gap-4 mb-6">
        <DocSelector value={docId} onChange={setDocId} className="flex-1 max-w-sm" />
        <div className="flex gap-2">
          {(["sentiment", "emotions"] as const).map(t => (
            <button key={t} onClick={() => setTab(t)}
              className={`px-4 py-2 rounded-xl text-sm font-medium transition-all ${
                tab === t ? "bg-brand-600 text-white" : "bg-white/5 text-slate-400 hover:text-white"
              }`}>
              {t.charAt(0).toUpperCase() + t.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {!docId && <div className="glass-card p-12 text-center text-slate-400">Select a document to analyze sentiment</div>}

      {/* Sentiment Tab */}
      {tab === "sentiment" && docId && sentLoading && <LoadingSpinner text="Analyzing sentiment…" />}
      {tab === "sentiment" && sentData && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            <KpiCard label="Overall Sentiment" value={sentData.document?.label?.toUpperCase()} color="green" delay={0.05} />
            <KpiCard label="Polarity" value={sentData.document?.polarity?.toFixed(3)} color="brand" delay={0.1} />
            <KpiCard label="Subjectivity" value={sentData.document?.subjectivity?.toFixed(3)} color="yellow" delay={0.15} />
            <KpiCard label="Mixed" value={sentData.mixed ? "Yes" : "No"} color="purple" delay={0.2} />
          </div>

          <div className="grid grid-cols-2 gap-6 mb-6">
            {/* Pie */}
            <div className="glass-card p-6">
              <h3 className="section-title">Sentiment Distribution</h3>
              <ResponsiveContainer width="100%" height={260}>
                <PieChart>
                  <Pie data={pieData} cx="50%" cy="50%" outerRadius={90} dataKey="value" label={({ name, value }) => `${name}: ${value}%`} labelLine>
                    {pieData.map((entry, i) => (
                      <Cell key={i} fill={(SENT_COLORS as any)[entry.name] || "#94a3b8"} />
                    ))}
                  </Pie>
                  <Tooltip contentStyle={{ background: "#1a1a2e", border: "1px solid #2d2d4a", borderRadius: 8 }} />
                </PieChart>
              </ResponsiveContainer>
            </div>

            {/* Trend */}
            <div className="glass-card p-6">
              <h3 className="section-title">Sentiment Trend</h3>
              <ResponsiveContainer width="100%" height={260}>
                <LineChart data={trendData}>
                  <XAxis dataKey="index" tick={{ fill: "#94a3b8", fontSize: 10 }} />
                  <YAxis domain={[-1, 1]} tick={{ fill: "#94a3b8", fontSize: 10 }} />
                  <Tooltip contentStyle={{ background: "#1a1a2e", border: "1px solid #2d2d4a", borderRadius: 8 }} />
                  <Line type="monotone" dataKey="polarity" stroke="#6366f1" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Sentence sentiments */}
          <div className="glass-card p-6">
            <h3 className="section-title">Sentence-Level Sentiments (top 20)</h3>
            <div className="space-y-2 max-h-80 overflow-y-auto">
              {(sentData.sentence_sentiments || []).slice(0, 20).map((s: any, i: number) => (
                <div key={i} className="flex items-start gap-3 p-3 rounded-lg bg-white/5">
                  <span className="shrink-0 text-xs px-2 py-0.5 rounded-full font-medium"
                    style={{ background: `${(SENT_COLORS as any)[s.label]}20`, color: (SENT_COLORS as any)[s.label] }}>
                    {s.label}
                  </span>
                  <span className="text-sm text-slate-300 flex-1">{s.text}</span>
                  <span className="text-xs text-slate-500 shrink-0">{s.polarity?.toFixed(2)}</span>
                </div>
              ))}
            </div>
          </div>
        </motion.div>
      )}

      {/* Emotions Tab */}
      {tab === "emotions" && docId && emotLoading && <LoadingSpinner text="Detecting emotions…" />}
      {tab === "emotions" && emotData && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
          <div className="grid grid-cols-2 gap-6">
            <div className="glass-card p-6">
              <h3 className="section-title">Emotion Radar</h3>
              <ResponsiveContainer width="100%" height={360}>
                <RadarChart data={emotData.radar || []}>
                  <PolarGrid stroke="#2d2d4a" />
                  <PolarAngleAxis dataKey="emotion" tick={{ fill: "#94a3b8", fontSize: 11 }} />
                  <Radar name="Score" dataKey="value" stroke="#6366f1" fill="#6366f1" fillOpacity={0.3} strokeWidth={2} />
                  <Tooltip contentStyle={{ background: "#1a1a2e", border: "1px solid #2d2d4a", borderRadius: 8 }} />
                </RadarChart>
              </ResponsiveContainer>
            </div>
            <div className="glass-card p-6">
              <h3 className="section-title">Emotion Breakdown</h3>
              <div className="space-y-3 mt-2">
                {(emotData.radar || []).map((e: any, i: number) => (
                  <div key={i} className="flex items-center gap-3">
                    <span className="text-sm text-slate-300 w-24 capitalize">{e.emotion}</span>
                    <div className="flex-1 bg-white/10 rounded-full h-2 overflow-hidden">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${e.value}%` }}
                        transition={{ delay: i * 0.05, duration: 0.6 }}
                        className="h-full rounded-full"
                        style={{ background: EMOTION_COLORS[i % EMOTION_COLORS.length] }}
                      />
                    </div>
                    <span className="text-xs text-slate-400 w-12 text-right">{e.value?.toFixed(1)}%</span>
                  </div>
                ))}
              </div>
              <div className="mt-6 p-4 rounded-xl bg-white/5 text-center">
                <div className="text-xs text-slate-400">Dominant Emotion</div>
                <div className="text-xl font-bold text-brand-300 capitalize mt-1">{emotData.dominant_emotion}</div>
              </div>
            </div>
          </div>
        </motion.div>
      )}
    </div>
  );
}
