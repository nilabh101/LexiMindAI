import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import { getDocumentDetail } from "../../lib/api";

export function DocumentDetailPage() {
  const { docId } = useParams<{ docId: string }>();
  const [data, setData] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!docId) return;
    getDocumentDetail(Number(docId))
      .then(r => setData(r.data))
      .catch(e => setError(e?.message || "Could not load document"));
  }, [docId]);

  if (error) return <div className="p-8 text-red-300 text-sm">{error}</div>;
  if (!data) return <div className="p-8 text-slate-400 text-sm">Loading document…</div>;

  const d = data.document || {};
  return (
    <div className="p-6 lg:p-8 max-w-4xl mx-auto">
      <Link to="/app/library" className="inline-flex items-center gap-1.5 text-slate-400 hover:text-white text-sm mb-6">
        <ArrowLeft size={14} /> Back to Library
      </Link>
      <h1 className="text-2xl font-bold text-white mb-2">{d.filename}</h1>
      <p className="text-sm text-slate-400 mb-6">
        {d.status} · {d.documentType || "UNKNOWN"} · {d.subject || "No subject"}
      </p>
      {d.ocrRequired && (
        <div className="mb-4 p-3 rounded-xl bg-orange-500/10 text-orange-200 text-sm">
          {d.ocrMessage || "This document requires OCR processing."}
        </div>
      )}
      {d.errorMessage && <div className="mb-4 text-sm text-red-300">{d.errorMessage}</div>}
      {d.classificationReason && <p className="text-xs text-slate-500 mb-6">{d.classificationReason}</p>}

      <section className="mb-8">
        <h2 className="font-semibold text-white mb-3">Pages</h2>
        <div className="space-y-3">
          {(data.pages || []).map((p: any) => (
            <div key={p.page} className="bg-white/3 border border-white/6 rounded-xl p-4">
              <div className="text-xs text-slate-500 mb-2">Page {p.page}</div>
              <pre className="text-xs text-slate-300 whitespace-pre-wrap max-h-48 overflow-y-auto">{p.cleanText || p.rawText || "No extractable text"}</pre>
            </div>
          ))}
          {(data.pages || []).length === 0 && <p className="text-slate-500 text-sm">No pages extracted.</p>}
        </div>
      </section>

      <section className="mb-8">
        <h2 className="font-semibold text-white mb-3">Detected chapters / topics / concepts</h2>
        <div className="flex flex-wrap gap-2">
          {(data.concepts || []).map((c: any) => (
            <span key={c.id} className="text-xs bg-white/8 text-slate-300 px-2 py-1 rounded-lg">
              {c.name}{c.page ? ` · p.${c.page}` : ""}{c.needsReview ? " · review" : ""}
            </span>
          ))}
          {(data.concepts || []).length === 0 && <p className="text-slate-500 text-sm">No concepts detected.</p>}
        </div>
      </section>

      <section>
        <h2 className="font-semibold text-white mb-3">Extracted questions</h2>
        <div className="space-y-3">
          {(data.questions || []).map((q: any) => (
            <div key={q.id} className="bg-white/3 border border-white/6 rounded-xl p-4 text-sm text-slate-200">
              <div className="text-xs text-slate-500 mb-1">
                {q.questionNumber ? `Q${q.questionNumber}` : "Question"} · {q.source}
                {q.year != null ? ` · ${q.year}` : ""}
                {q.marks != null ? ` · ${q.marks} marks` : ""}
                {q.needsReview ? " · needs review" : ""}
              </div>
              {q.question}
            </div>
          ))}
          {(data.questions || []).length === 0 && <p className="text-slate-500 text-sm">No questions extracted from this document.</p>}
        </div>
      </section>
    </div>
  );
}
