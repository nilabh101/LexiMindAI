import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { Brain } from "lucide-react";
import {
  RadarChart, Radar, PolarGrid, PolarAngleAxis, ResponsiveContainer, Tooltip
} from "recharts";
import { getDNA, getStyle } from "../lib/api";
import { DocSelector } from "../components/DocSelector";
import { LoadingSpinner } from "../components/LoadingSpinner";
import { PageHeader } from "../components/PageHeader";

export function DNAPage() {
  const [docId, setDocId] = useState<number | null>(null);

  const { data: dnaData, isLoading: dnaLoading } = useQuery({
    queryKey: ["dna", docId],
    queryFn: () => getDNA(docId!).then(r => r.data),
    enabled: !!docId,
  });

  const { data: styleData, isLoading: styleLoading } = useQuery({
    queryKey: ["style", docId],
    queryFn: () => getStyle(docId!).then(r => r.data),
    enabled: !!docId,
  });

  const isLoading = dnaLoading || styleLoading;

  return (
    <div className="p-8">
      <PageHeader
        title="Document DNA"
        subtitle="Unique document fingerprint across 8 linguistic dimensions"
        icon={<Brain size={22} />}
      />

      <DocSelector value={docId} onChange={setDocId} className="max-w-sm mb-6" />

      {!docId && <div className="glass-card p-12 text-center text-slate-400">Select a document to generate its DNA</div>}
      {docId && isLoading && <LoadingSpinner text="Generating Document DNA…" />}

      {dnaData && styleData && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
          {/* DNA Header */}
          <div className="glass-card p-6 mb-6 bg-gradient-to-r from-brand-500/10 to-purple-500/10 border border-brand-500/20">
            <div className="flex items-center gap-6">
              <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-brand-500 to-purple-500 flex items-center justify-center shadow-lg shadow-brand-500/30">
                <Brain size={28} className="text-white" />
              </div>
              <div>
                <h2 className="text-xl font-bold text-white">Document Fingerprint</h2>
                <p className="text-sm text-slate-400 mt-0.5">
                  Style: <span className="text-brand-300 font-medium">{styleData.primary_style}</span>
                  {" · "}Dominant trait: <span className="text-purple-300 font-medium capitalize">{dnaData.dominant_trait?.replace(/_/g, " ")}</span>
                </p>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-6 mb-6">
            {/* Radar */}
            <div className="glass-card p-6">
              <h3 className="section-title">DNA Radar</h3>
              <ResponsiveContainer width="100%" height={360}>
                <RadarChart data={dnaData.radar || []}>
                  <PolarGrid stroke="#2d2d4a" />
                  <PolarAngleAxis dataKey="dimension" tick={{ fill: "#94a3b8", fontSize: 10 }} />
                  <Radar name="DNA" dataKey="value" stroke="#6366f1" fill="#6366f1" fillOpacity={0.35} strokeWidth={2} />
                  <Tooltip contentStyle={{ background: "#1a1a2e", border: "1px solid #2d2d4a", borderRadius: 8 }} />
                </RadarChart>
              </ResponsiveContainer>
            </div>

            {/* Dimension bars */}
            <div className="glass-card p-6">
              <h3 className="section-title">Dimension Scores</h3>
              <div className="space-y-3">
                {(dnaData.radar || []).map((d: any, i: number) => (
                  <div key={i}>
                    <div className="flex justify-between text-xs mb-1">
                      <span className="text-slate-300">{d.dimension}</span>
                      <span className="text-brand-300 font-medium">{d.value?.toFixed(1)}%</span>
                    </div>
                    <div className="bg-white/10 rounded-full h-2 overflow-hidden">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${d.value}%` }}
                        transition={{ delay: i * 0.06, duration: 0.7 }}
                        className="h-full rounded-full bg-gradient-to-r from-brand-500 to-purple-500"
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Style analysis */}
          <div className="glass-card p-6 mb-6">
            <h3 className="section-title">Writing Style Analysis</h3>
            <div className="grid grid-cols-2 gap-6">
              <div>
                <div className="text-4xl font-bold gradient-text mb-1">{styleData.primary_style}</div>
                <div className="text-sm text-slate-400">{styleData.description}</div>
                <div className="mt-4 text-sm">
                  <span className="text-slate-400">Confidence: </span>
                  <span className="text-brand-300 font-semibold">{styleData.confidence}%</span>
                </div>
              </div>
              <div className="space-y-2">
                {(styleData.scores || []).slice(0, 6).map((s: any, i: number) => (
                  <div key={i} className="flex items-center gap-3">
                    <span className="text-xs text-slate-400 w-24">{s.style}</span>
                    <div className="flex-1 bg-white/10 rounded-full h-1.5">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${s.score}%` }}
                        transition={{ delay: i * 0.05 }}
                        className="h-full rounded-full bg-gradient-to-r from-brand-500 to-purple-500"
                      />
                    </div>
                    <span className="text-xs text-slate-400 w-10 text-right">{s.score}%</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Style metrics */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {Object.entries(styleData.metrics || {}).map(([k, v]: any, i) => (
              <motion.div
                key={k}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.07 }}
                className="glass-card p-4 text-center"
              >
                <div className="text-xl font-bold text-brand-300">{typeof v === "number" ? v.toFixed(2) : v}</div>
                <div className="text-xs text-slate-400 mt-1 capitalize">{k.replace(/_/g, " ")}</div>
              </motion.div>
            ))}
          </div>
        </motion.div>
      )}
    </div>
  );
}
