import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { Layers, Tag, Building2, MapPin, Calendar, User } from "lucide-react";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell,
} from "recharts";
import { getTopics, getEntities } from "../lib/api";
import { DocSelector } from "../components/DocSelector";
import { LoadingSpinner } from "../components/LoadingSpinner";
import { PageHeader } from "../components/PageHeader";

const COLORS = ["#6366f1","#8b5cf6","#ec4899","#f59e0b","#10b981","#06b6d4","#f97316","#ef4444"];

const ENTITY_ICONS: Record<string, any> = {
  People: User, PERSON: User,
  Organizations: Building2, ORG: Building2,
  Locations: MapPin, GPE: MapPin,
  Dates: Calendar, DATE: Calendar,
  Events: Tag, EVENT: Tag,
  Products: Tag, PRODUCT: Tag,
  Named: Tag, OTHER: Tag,
  TECHNOLOGY: Tag,
};

export function TopicsPage() {
  const [docId, setDocId] = useState<number | null>(null);
  const [tab, setTab] = useState<"topics" | "entities">("topics");

  // API returns: { document_id, topics: { primary_topics, secondary_topics, topics: [...], total_detected }, keywords: [...] }
  const { data: topicData, isLoading: topicLoading } = useQuery({
    queryKey: ["topics", docId],
    queryFn: () => getTopics(docId!),
    enabled: !!docId,
    select: (r: any) => r.data ?? r,
  });

  // API returns: { document_id, entities: {...}, total_unique_entities, categories: [...] }
  const { data: entityData, isLoading: entityLoading } = useQuery({
    queryKey: ["entities", docId],
    queryFn: () => getEntities(docId!),
    enabled: !!docId && tab === "entities",
    select: (r: any) => r.data ?? r,
  });

  // Normalise topics data — handle both shapes
  const topicsObj = topicData?.topics;                         // the nested object from detect_topics
  const topicsList: any[] = Array.isArray(topicsObj)          // if topics IS the array
    ? topicsObj
    : (topicsObj?.topics ?? []);                              // or the .topics sub-array
  const primaryTopics: string[] = Array.isArray(topicsObj)
    ? []
    : (topicsObj?.primary_topics ?? []);
  const secondaryTopics: string[] = Array.isArray(topicsObj)
    ? []
    : (topicsObj?.secondary_topics ?? []);
  const keywords: any[] = topicData?.keywords ?? [];

  // Normalise entities
  const categories: any[] = entityData?.categories ?? (() => {
    // Fallback: build categories from entities object
    const ents = entityData?.entities ?? {};
    return Object.entries(ents)
      .filter(([, v]) => Array.isArray(v) && (v as any[]).length > 0)
      .map(([k, v]) => ({ type: k, count: (v as any[]).length, items: v }));
  })();

  return (
    <div className="p-8">
      <PageHeader
        title="Topics & Entity Extraction"
        subtitle="AI-powered topic detection and named entity recognition"
        icon={<Layers size={22} />}
      />

      <div className="flex items-center gap-4 mb-6">
        <DocSelector value={docId} onChange={setDocId} className="flex-1 max-w-sm" />
        <div className="flex gap-2">
          {(["topics", "entities"] as const).map(t => (
            <button key={t} onClick={() => setTab(t)}
              className={`px-4 py-2 rounded-xl text-sm font-medium transition-all ${tab === t ? "bg-brand-600 text-white" : "bg-white/5 text-slate-400 hover:text-white"}`}>
              {t.charAt(0).toUpperCase() + t.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {!docId && (
        <div className="glass-card p-12 text-center text-slate-400">Select a document to detect topics and entities</div>
      )}

      {/* ─── Topics ─── */}
      {tab === "topics" && docId && topicLoading && <LoadingSpinner text="Detecting topics…" />}
      {tab === "topics" && topicData && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>

          {/* Topic chips */}
          {(primaryTopics.length > 0 || secondaryTopics.length > 0) && (
            <div className="flex flex-wrap gap-3 mb-6">
              {primaryTopics.map((t: string, i: number) => (
                <span key={i} className="px-4 py-2 rounded-full text-sm font-semibold bg-brand-600/30 text-brand-300 border border-brand-500/30">
                  🏷️ {t}
                </span>
              ))}
              {secondaryTopics.map((t: string, i: number) => (
                <span key={i} className="px-4 py-2 rounded-full text-sm font-medium bg-white/10 text-slate-300 border border-white/10">
                  {t}
                </span>
              ))}
            </div>
          )}

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
            {/* Topic score bar chart */}
            {topicsList.length > 0 && (
              <div className="glass-card p-6">
                <h3 className="section-title mb-4">Topic Scores</h3>
                <ResponsiveContainer width="100%" height={280}>
                  <BarChart data={topicsList} layout="vertical" margin={{ left: 90 }}>
                    <XAxis type="number" tick={{ fill: "#94a3b8", fontSize: 10 }} />
                    <YAxis dataKey="topic" type="category" tick={{ fill: "#94a3b8", fontSize: 11 }} width={85} />
                    <Tooltip contentStyle={{ background: "#1a1a2e", border: "1px solid #2d2d4a", borderRadius: 8 }} />
                    <Bar dataKey="score" radius={[0, 4, 4, 0]}>
                      {topicsList.map((_: any, i: number) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}

            {/* TF-IDF keywords */}
            {keywords.length > 0 && (
              <div className="glass-card p-6">
                <h3 className="section-title mb-4">Top Keywords (TF-IDF)</h3>
                <div className="space-y-2 max-h-72 overflow-y-auto">
                  {keywords.slice(0, 20).map((kw: any, i: number) => {
                    const maxScore = keywords[0]?.score || 1;
                    const pct = Math.min(100, (kw.score / maxScore) * 100);
                    return (
                      <div key={i} className="flex items-center gap-3">
                        <span className="text-xs text-slate-500 w-6 text-right">#{kw.rank ?? i + 1}</span>
                        <div className="flex-1 bg-white/10 rounded-full h-1.5 overflow-hidden">
                          <motion.div initial={{ width: 0 }} animate={{ width: `${pct}%` }} transition={{ delay: i * 0.02 }}
                            className="h-full rounded-full bg-gradient-to-r from-brand-500 to-purple-500" />
                        </div>
                        <span className="text-sm text-white w-28 text-right font-medium">{kw.keyword}</span>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </div>

          {/* Topic detail cards */}
          {topicsList.length > 0 && (
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
              {topicsList.slice(0, 8).map((t: any, i: number) => (
                <motion.div key={i} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.04 }}
                  className="glass-card p-4">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-semibold text-white text-sm">{t.topic}</span>
                    <span className="text-xs px-2 py-0.5 rounded-full" style={{ background: `${COLORS[i % COLORS.length]}30`, color: COLORS[i % COLORS.length] }}>
                      #{t.rank ?? i + 1}
                    </span>
                  </div>
                  <div className="text-xs text-slate-400 mb-2">Score: {typeof t.score === "number" ? t.score.toFixed(2) : t.score}</div>
                  {Array.isArray(t.keywords) && (
                    <div className="flex flex-wrap gap-1">
                      {t.keywords.slice(0, 3).map((kw: string, j: number) => (
                        <span key={j} className="text-xs px-2 py-0.5 rounded bg-white/10 text-slate-300">{kw}</span>
                      ))}
                    </div>
                  )}
                </motion.div>
              ))}
            </div>
          )}

          {topicsList.length === 0 && keywords.length === 0 && (
            <div className="glass-card p-10 text-center text-slate-400 text-sm">
              No topics detected. The document may be too short or contain mostly numbers/symbols.
            </div>
          )}
        </motion.div>
      )}

      {/* ─── Entities ─── */}
      {tab === "entities" && docId && entityLoading && <LoadingSpinner text="Extracting entities…" />}
      {tab === "entities" && entityData && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
          {categories.length === 0 ? (
            <div className="glass-card p-10 text-center text-slate-400 text-sm">
              No named entities detected. Try a document with names, places, organisations, or dates.
            </div>
          ) : (
            <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
              {categories.map((cat: any, i: number) => {
                const Icon = ENTITY_ICONS[cat.type] || Tag;
                return (
                  <motion.div key={i} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.06 }}
                    className="glass-card p-4">
                    <div className="flex items-center gap-2 mb-3">
                      <Icon size={14} className="text-brand-400" />
                      <span className="font-semibold text-white text-sm">{cat.type}</span>
                      <span className="ml-auto text-xs text-slate-500">{cat.count} found</span>
                    </div>
                    <div className="space-y-1.5">
                      {(Array.isArray(cat.items) ? cat.items : []).slice(0, 8).map((item: any, j: number) => (
                        <div key={j} className="flex items-center justify-between text-xs">
                          <span className="text-slate-300 truncate max-w-[70%]">
                            {typeof item === "string" ? item : item?.text ?? ""}
                          </span>
                          {item?.count && <span className="text-slate-500">{item.count}×</span>}
                        </div>
                      ))}
                    </div>
                  </motion.div>
                );
              })}
            </div>
          )}
        </motion.div>
      )}
    </div>
  );
}
