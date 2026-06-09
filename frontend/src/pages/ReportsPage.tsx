import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { FileText, Download, Loader2 } from "lucide-react";
import { listDocuments, downloadReport, getFullAnalysis } from "../lib/api";
import { PageHeader } from "../components/PageHeader";
import { LoadingSpinner } from "../components/LoadingSpinner";
import { DocSelector } from "../components/DocSelector";
import { KpiCard } from "../components/KpiCard";
import { formatDate, formatNumber, downloadBlob } from "../lib/utils";
import toast from "react-hot-toast";

export function ReportsPage() {
  const [docId, setDocId] = useState<number | null>(null);
  const [downloading, setDownloading] = useState(false);

  const { data: fullData, isLoading } = useQuery({
    queryKey: ["full", docId],
    queryFn: () => getFullAnalysis(docId!).then(r => r.data),
    enabled: !!docId,
  });

  const handleDownload = async () => {
    if (!docId) return;
    setDownloading(true);
    try {
      const res = await downloadReport(docId);
      downloadBlob(res.data, `LexiMind_Report_${docId}.pdf`);
      toast.success("Report downloaded");
    } catch (e: any) {
      toast.error("Failed to generate report: " + e.message);
    } finally {
      setDownloading(false);
    }
  };

  return (
    <div className="p-8">
      <PageHeader
        title="Report Generation"
        subtitle="Download comprehensive PDF reports with all analytics"
        icon={<FileText size={22} />}
        actions={
          docId ? (
            <button
              onClick={handleDownload}
              disabled={downloading}
              className="btn-primary flex items-center gap-2"
            >
              {downloading ? <Loader2 size={16} className="animate-spin" /> : <Download size={16} />}
              {downloading ? "Generating…" : "Download PDF"}
            </button>
          ) : undefined
        }
      />

      <DocSelector value={docId} onChange={setDocId} className="max-w-sm mb-6" />

      {!docId && <div className="glass-card p-12 text-center text-slate-400">Select a document to preview and download report</div>}
      {docId && isLoading && <LoadingSpinner text="Loading full analysis…" />}

      {fullData && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
          {/* Stats KPIs */}
          <div className="grid grid-cols-2 lg:grid-cols-5 gap-4 mb-6">
            <KpiCard label="Words" value={formatNumber(fullData.stats?.word_count || 0)} color="brand" delay={0.05} />
            <KpiCard label="Unique" value={formatNumber(fullData.stats?.unique_word_count || 0)} color="blue" delay={0.1} />
            <KpiCard label="Sentences" value={formatNumber(fullData.stats?.sentence_count || 0)} color="purple" delay={0.15} />
            <KpiCard label="Grade Level" value={fullData.stats?.reading_grade_level || 0} color="yellow" delay={0.2} />
            <KpiCard label="Read Time" value={`${fullData.stats?.reading_time_minutes || 0} min`} color="green" delay={0.25} />
          </div>

          {/* Report sections preview */}
          <div className="grid grid-cols-2 gap-6 mb-6">
            {/* Sentiment preview */}
            <div className="glass-card p-5">
              <h3 className="font-semibold text-white mb-3">Sentiment</h3>
              <div className="flex items-center gap-4">
                <div className="text-3xl font-bold text-emerald-400 capitalize">
                  {fullData.sentiment?.document?.label}
                </div>
                <div className="text-sm text-slate-400">
                  Polarity: {fullData.sentiment?.document?.polarity?.toFixed(3)}
                </div>
              </div>
            </div>

            {/* Topics preview */}
            <div className="glass-card p-5">
              <h3 className="font-semibold text-white mb-3">Primary Topics</h3>
              <div className="flex flex-wrap gap-2">
                {(fullData.topics?.topics?.primary_topics || []).map((t: string, i: number) => (
                  <span key={i} className="px-3 py-1 rounded-full text-xs bg-brand-600/30 text-brand-300 border border-brand-500/30">{t}</span>
                ))}
              </div>
            </div>
          </div>

          {/* AI Insights */}
          <div className="glass-card p-6 mb-6">
            <h3 className="section-title">AI Insights Preview</h3>
            <div className="grid grid-cols-1 gap-3">
              {(fullData.insights || []).slice(0, 6).map((ins: any, i: number) => (
                <motion.div key={i} initial={{ opacity: 0, x: -8 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.05 }}
                  className="flex gap-3 p-3 rounded-xl bg-white/5">
                  <span className="text-xl shrink-0">{ins.icon}</span>
                  <p className="text-sm text-slate-300">{ins.insight}</p>
                </motion.div>
              ))}
            </div>
          </div>

          {/* Top words preview */}
          <div className="glass-card p-6 mb-6">
            <h3 className="section-title">Top Words</h3>
            <div className="flex flex-wrap gap-2">
              {(fullData.word_frequency || []).slice(0, 20).map((w: any, i: number) => (
                <span key={i} className="px-3 py-1 rounded-lg bg-white/10 text-sm text-slate-300">
                  {w.word} <span className="text-brand-400 font-semibold">{w.count}</span>
                </span>
              ))}
            </div>
          </div>

          {/* Download button */}
          <div className="flex justify-center">
            <button
              onClick={handleDownload}
              disabled={downloading}
              className="btn-primary text-lg px-8 py-3 flex items-center gap-3"
            >
              {downloading ? <Loader2 size={20} className="animate-spin" /> : <Download size={20} />}
              {downloading ? "Generating PDF Report…" : "Download Full PDF Report"}
            </button>
          </div>
        </motion.div>
      )}
    </div>
  );
}
