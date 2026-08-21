import { useState, useCallback, useEffect } from "react";
import { Link } from "react-router-dom";
import { useDropzone } from "react-dropzone";
import { motion, AnimatePresence } from "framer-motion";
import { Library, Upload, CheckCircle, Clock, AlertCircle, Trash2, RotateCcw, ChevronRight } from "lucide-react";
import type { LibraryDocument, DocumentStatus } from "../../types/education";
import { formatBytes } from "../../lib/utils";
import { listDocuments, deleteDocument, retryDocument, uploadLibraryDocument, mapDocStatus } from "../../lib/api";
import { loadUser } from "../../store/userStore";
import { SUBJECTS } from "../../data/curriculum";
import toast from "react-hot-toast";

const STATUS_CONFIG: Record<DocumentStatus, { label: string; color: string; icon: React.ReactNode }> = {
  uploaded:     { label: "Uploaded",     color: "text-blue-300",    icon: <Clock size={12} /> },
  processing:   { label: "Processing",   color: "text-amber-300",   icon: <Clock size={12} className="animate-spin" /> },
  ready:        { label: "Ready",        color: "text-emerald-300", icon: <CheckCircle size={12} /> },
  failed:       { label: "Failed",       color: "text-red-300",     icon: <AlertCircle size={12} /> },
  needs_review: { label: "Needs Review", color: "text-orange-300",  icon: <AlertCircle size={12} /> },
};

const FILE_ICONS: Record<string, string> = {
  pdf: "📕", pptx: "📊", docx: "📘", txt: "📄",
};

function toLibraryDoc(d: any): LibraryDocument {
  return {
    id: String(d.id),
    name: d.original_filename || d.filename,
    fileType: (d.file_type || "pdf") as LibraryDocument["fileType"],
    fileSize: d.file_size,
    uploadedAt: d.upload_date,
    subjectId: d.subject_id,
    subject: d.subject,
    documentType: d.document_type,
    status: mapDocStatus(d.status),
    errorMessage: d.error_message,
    ocrRequired: d.ocr_required,
  };
}

export function LibraryPage() {
  const user = loadUser();
  const [docs, setDocs] = useState<LibraryDocument[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [subjectId, setSubjectId] = useState(user?.academicProfile?.subjectIds?.[0] ?? "");
  const [docType, setDocType] = useState("");
  const [busy, setBusy] = useState(false);

  const refresh = useCallback(async () => {
    try {
      const res = await listDocuments();
      setDocs((res.data || []).map(toLibraryDoc));
      setError(null);
    } catch (e: any) {
      setError(e?.message || "Could not load library");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { refresh(); }, [refresh]);

  useEffect(() => {
    const pending = docs.some(d => d.status === "processing" || d.status === "uploaded");
    if (!pending) return;
    const t = setInterval(refresh, 2500);
    return () => clearInterval(t);
  }, [docs, refresh]);

  const onDrop = useCallback(async (accepted: File[]) => {
    setBusy(true);
    try {
      for (const file of accepted) {
        const sub = SUBJECTS.find(s => s.id === subjectId);
        await uploadLibraryDocument(file, {
          user_id: user?.id || "",
          education_level: user?.academicProfile?.educationLevel || "",
          class_or_year: user?.academicProfile?.year != null ? String(user.academicProfile.year) : "",
          course: user?.academicProfile?.courseId || "",
          subject_id: subjectId,
          subject: sub?.name || "",
          document_type: docType,
        });
      }
      await refresh();
    } catch (e: any) {
      toast.error(e?.message || "Upload failed");
    } finally {
      setBusy(false);
    }
  }, [docType, refresh, subjectId, user]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    maxSize: 500 * 1024 * 1024,
    accept: {
      "application/pdf": [".pdf"],
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
      "text/plain": [".txt"],
    },
  });

  const removeDoc = async (id: string) => {
    try {
      await deleteDocument(Number(id));
      setDocs(prev => prev.filter(d => d.id !== id));
    } catch (e: any) {
      toast.error(e?.message || "Delete failed");
    }
  };

  const retry = async (id: string) => {
    try {
      await retryDocument(Number(id));
      await refresh();
    } catch (e: any) {
      toast.error(e?.message || "Retry failed");
    }
  };

  return (
    <div className="p-6 lg:p-8 max-w-4xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white">My Library</h1>
        <p className="text-slate-400 text-sm mt-1">Upload your notes, PDFs, and study materials.</p>
      </div>

      <div className="bg-white/3 border border-white/6 rounded-2xl p-4 mb-4 flex flex-wrap gap-3">
        <select value={subjectId} onChange={e => setSubjectId(e.target.value)}
          className="bg-white/5 border border-white/10 rounded-xl px-3 py-2 text-sm text-slate-300 outline-none">
          <option value="">Subject (optional)</option>
          {SUBJECTS.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
        </select>
        <select value={docType} onChange={e => setDocType(e.target.value)}
          className="bg-white/5 border border-white/10 rounded-xl px-3 py-2 text-sm text-slate-300 outline-none">
          <option value="">Type (auto-detect)</option>
          <option value="STUDY_NOTES">Study notes</option>
          <option value="PYQ">Previous year questions</option>
          <option value="QUESTION_BANK">Question bank</option>
          <option value="REFERENCE">Reference</option>
        </select>
      </div>

      <div {...getRootProps()}
        className={`border-2 border-dashed rounded-2xl p-10 text-center cursor-pointer transition-all mb-8 ${isDragActive ? "border-indigo-500 bg-indigo-500/8" : "border-white/10 hover:border-indigo-500/40 hover:bg-white/2"}`}>
        <input {...getInputProps()} />
        <Upload size={36} className={`mx-auto mb-4 ${isDragActive ? "text-indigo-400" : "text-slate-500"}`} />
        <p className="text-white font-semibold text-base">{busy ? "Uploading…" : isDragActive ? "Drop files here" : "Drag & drop your files here"}</p>
        <p className="text-slate-400 text-sm mt-2">or click to browse · PDF, DOCX, TXT · up to 500 MB</p>
        <div className="flex justify-center gap-3 mt-4">
          {["pdf","docx","txt"].map(ext => (
            <span key={ext} className="px-3 py-1 rounded-lg bg-white/5 text-xs font-mono text-slate-400">.{ext}</span>
          ))}
        </div>
      </div>

      {error && <p className="text-sm text-red-300 mb-4">{error}</p>}

      {loading ? (
        <p className="text-slate-500 text-sm">Loading library…</p>
      ) : docs.length === 0 ? (
        <div className="bg-white/3 border border-white/6 rounded-2xl p-12 text-center">
          <Library size={36} className="text-slate-600 mx-auto mb-3" />
          <p className="text-slate-400">Your library is empty. Upload your first document above.</p>
        </div>
      ) : (
        <div className="space-y-2.5">
          <AnimatePresence>
            {docs.map((doc) => {
              const sc = STATUS_CONFIG[doc.status] ?? STATUS_CONFIG.uploaded;
              return (
                <motion.div key={doc.id} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, x: -20 }}
                  className="bg-white/3 border border-white/6 rounded-2xl p-5 flex items-center gap-4">
                  <div className="text-2xl shrink-0">{FILE_ICONS[doc.fileType] ?? "📄"}</div>
                  <Link to={`/app/library/${doc.id}`} className="flex-1 min-w-0">
                    <div className="font-medium text-white truncate hover:text-indigo-300">{doc.name}</div>
                    <div className="text-xs text-slate-500 mt-0.5">
                      {formatBytes(doc.fileSize)}
                      {doc.documentType ? ` · ${doc.documentType}` : ""}
                      {doc.subject ? ` · ${doc.subject}` : ""}
                      {doc.uploadedAt ? ` · ${new Date(doc.uploadedAt).toLocaleDateString()}` : ""}
                    </div>
                    {doc.errorMessage && <div className="text-xs text-red-300 mt-1">{doc.errorMessage}</div>}
                    {doc.ocrRequired && <div className="text-xs text-orange-300 mt-1">This document requires OCR processing.</div>}
                  </Link>
                  <div className={`flex items-center gap-1.5 text-xs font-medium ${sc.color} shrink-0`}>
                    {sc.icon} {sc.label}
                  </div>
                  {(doc.status === "failed" || doc.status === "needs_review") && (
                    <button onClick={() => retry(doc.id)} className="text-slate-500 hover:text-indigo-300" title="Retry processing">
                      <RotateCcw size={15} />
                    </button>
                  )}
                  <Link to={`/app/library/${doc.id}`} className="text-slate-600 hover:text-indigo-400"><ChevronRight size={16} /></Link>
                  <button onClick={() => removeDoc(doc.id)} className="text-slate-600 hover:text-red-400 transition-colors shrink-0">
                    <Trash2 size={15} />
                  </button>
                </motion.div>
              );
            })}
          </AnimatePresence>
        </div>
      )}
    </div>
  );
}
