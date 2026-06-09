import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { BookOpen, Copy, Check } from "lucide-react";
import { getSummary } from "../lib/api";
import { DocSelector } from "../components/DocSelector";
import { LoadingSpinner } from "../components/LoadingSpinner";
import { PageHeader } from "../components/PageHeader";
import toast from "react-hot-toast";

export function SummaryPage() {
  const [docId, setDocId] = useState<number | null>(null);
  const [copied, setCopied] = useState<string | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ["summary", docId],
    queryFn: () => getSummary(docId!).then(r => r.data),
    enabled: !!docId,
  });

  const copyText = (text: string, key: string) => {
    navigator.clipboard.writeText(text);
    setCopied(key);
    toast.success("Copied to clipboard");
    setTimeout(() => setCopied(null), 2000);
  };

  const summaries = data ? [
    { key: "50", label: "50-Word Summary", content: data.summary_50, words: data.word_counts?.["50_word"] },
    { key: "100", label: "100-Word Summary", content: data.summary_100, words: data.word_counts?.["100_word"] },
    { key: "250", label: "250-Word Summary", content: data.summary_250, words: data.word_counts?.["250_word"] },
    { key: "exec", label: "Executive Summary", content: data.executive_summary, words: null },
    { key: "research", label: "Research Summary", content: data.research_summary, words: null },
  ] : [];

  return (
    <div className="p-8">
      <PageHeader
        title="AI Summary Generator"
        subtitle="Extractive summaries at multiple lengths, executive and research formats"
        icon={<BookOpen size={22} />}
      />

      <DocSelector value={docId} onChange={setDocId} className="max-w-sm mb-6" />

      {!docId && <div className="glass-card p-12 text-center text-slate-400">Select a document to generate summaries</div>}
      {docId && isLoading && <LoadingSpinner text="Generating summaries…" />}

      {data && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
          {/* Bullet points */}
          <div className="glass-card p-6 mb-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="section-title mb-0">Key Bullet Points</h3>
              <button
                onClick={() => copyText((data.bullet_points || []).join("\n"), "bullets")}
                className="btn-ghost text-xs flex items-center gap-1"
              >
                {copied === "bullets" ? <Check size={12} /> : <Copy size={12} />}
                Copy
              </button>
            </div>
            <ul className="space-y-2">
              {(data.bullet_points || []).map((bp: string, i: number) => (
                <motion.li
                  key={i}
                  initial={{ opacity: 0, x: -8 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.06 }}
                  className="flex gap-3 text-sm text-slate-300"
                >
                  <span className="text-brand-400 mt-0.5 shrink-0">•</span>
                  {bp}
                </motion.li>
              ))}
            </ul>
          </div>

          {/* Summary cards */}
          <div className="grid grid-cols-1 gap-4">
            {summaries.map(({ key, label, content, words }, i) => (
              <motion.div
                key={key}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.08 }}
                className="glass-card p-6"
              >
                <div className="flex items-center justify-between mb-3">
                  <h3 className="font-semibold text-white">{label}</h3>
                  <div className="flex items-center gap-3">
                    {words && <span className="text-xs text-slate-500">{words} words</span>}
                    <button
                      onClick={() => copyText(content || "", key)}
                      className="btn-ghost text-xs flex items-center gap-1"
                    >
                      {copied === key ? <Check size={12} /> : <Copy size={12} />}
                      Copy
                    </button>
                  </div>
                </div>
                <p className="text-sm text-slate-300 leading-relaxed">{content}</p>
              </motion.div>
            ))}
          </div>
        </motion.div>
      )}
    </div>
  );
}
