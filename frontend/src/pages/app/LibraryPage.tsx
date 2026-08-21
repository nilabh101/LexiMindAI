import { useState, useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { motion, AnimatePresence } from "framer-motion";
import { Library, Upload, FileText, CheckCircle, Clock, AlertCircle, Trash2 } from "lucide-react";
import type { LibraryDocument, DocumentStatus } from "../../types/education";
import { formatBytes } from "../../lib/utils";

const STATUS_CONFIG: Record<DocumentStatus, { label: string; color: string; icon: React.ReactNode }> = {
  uploaded:   { label: "Uploaded",   color: "text-blue-300",    icon: <Clock size={12} /> },
  processing: { label: "Processing", color: "text-amber-300",   icon: <Clock size={12} className="animate-spin" /> },
  ready:      { label: "Ready",      color: "text-emerald-300", icon: <CheckCircle size={12} /> },
  failed:     { label: "Failed",     color: "text-red-300",     icon: <AlertCircle size={12} /> },
};

const FILE_ICONS: Record<string, string> = {
  pdf: "📕", pptx: "📊", docx: "📘", txt: "📄",
};

export function LibraryPage() {
  const [docs, setDocs] = useState<LibraryDocument[]>([]);

  const onDrop = useCallback((accepted: File[]) => {
    const newDocs: LibraryDocument[] = accepted.map(f => ({
      id: `doc-${Date.now()}-${Math.random()}`,
      name: f.name,
      fileType: (f.name.split(".").pop()?.toLowerCase() ?? "pdf") as any,
      fileSize: f.size,
      uploadedAt: new Date().toISOString(),
      status: "uploaded",
    }));
    setDocs(prev => [...prev, ...newDocs]);
    // Simulate processing status change
    setTimeout(() => {
      setDocs(prev => prev.map(d =>
        newDocs.find(n => n.id === d.id) ? { ...d, status: "processing" } : d
      ));
    }, 800);
    setTimeout(() => {
      setDocs(prev => prev.map(d =>
        newDocs.find(n => n.id === d.id) ? { ...d, status: "ready" } : d
      ));
    }, 3000);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    maxSize: 500 * 1024 * 1024,
    accept: {
      "application/pdf": [".pdf"],
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
      "text/plain": [".txt"],
    },
  });

  const removeDoc = (id: string) => setDocs(prev => prev.filter(d => d.id !== id));

  return (
    <div className="p-6 lg:p-8 max-w-4xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white">My Library</h1>
        <p className="text-slate-400 text-sm mt-1">Upload your notes, PDFs, and study materials.</p>
      </div>

      {/* Drop zone */}
      <div {...getRootProps()}
        className={`border-2 border-dashed rounded-2xl p-10 text-center cursor-pointer transition-all mb-8 ${isDragActive ? "border-indigo-500 bg-indigo-500/8" : "border-white/10 hover:border-indigo-500/40 hover:bg-white/2"}`}>
        <input {...getInputProps()} />
        <Upload size={36} className={`mx-auto mb-4 ${isDragActive ? "text-indigo-400" : "text-slate-500"}`} />
        <p className="text-white font-semibold text-base">{isDragActive ? "Drop files here" : "Drag & drop your files here"}</p>
        <p className="text-slate-400 text-sm mt-2">or click to browse · PDF, DOCX, TXT · up to 500 MB</p>
        <div className="flex justify-center gap-3 mt-4">
          {["pdf","docx","txt"].map(ext => (
            <span key={ext} className="px-3 py-1 rounded-lg bg-white/5 text-xs font-mono text-slate-400">.{ext}</span>
          ))}
        </div>
      </div>

      {/* Documents */}
      {docs.length === 0 ? (
        <div className="bg-white/3 border border-white/6 rounded-2xl p-12 text-center">
          <Library size={36} className="text-slate-600 mx-auto mb-3" />
          <p className="text-slate-400">Your library is empty. Upload your first document above.</p>
        </div>
      ) : (
        <div className="space-y-2.5">
          <AnimatePresence>
            {docs.map((doc) => {
              const sc = STATUS_CONFIG[doc.status];
              return (
                <motion.div key={doc.id} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, x: -20 }}
                  className="bg-white/3 border border-white/6 rounded-2xl p-5 flex items-center gap-4">
                  <div className="text-2xl shrink-0">{FILE_ICONS[doc.fileType] ?? "📄"}</div>
                  <div className="flex-1 min-w-0">
                    <div className="font-medium text-white truncate">{doc.name}</div>
                    <div className="text-xs text-slate-500 mt-0.5">{formatBytes(doc.fileSize)}</div>
                  </div>
                  <div className={`flex items-center gap-1.5 text-xs font-medium ${sc.color} shrink-0`}>
                    {sc.icon} {sc.label}
                  </div>
                  <button onClick={() => removeDoc(doc.id)} className="text-slate-600 hover:text-red-400 transition-colors shrink-0">
                    <Trash2 size={15} />
                  </button>
                </motion.div>
              );
            })}
          </AnimatePresence>
        </div>
      )}

      <p className="text-xs text-slate-600 text-center mt-6">
        Note: document processing (text extraction, concept linking) will be active in Phase 2.
        Files are accepted and stored — AI analysis will connect them to your curriculum automatically.
      </p>
    </div>
  );
}
