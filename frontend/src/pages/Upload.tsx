import { useState } from "react";
import { useDropzone } from "react-dropzone";
import { AnimatePresence, motion } from "framer-motion";
import { Upload as UploadIcon, FileText, CheckCircle2, AlertCircle, Trash2, ArrowRight } from "lucide-react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "react-hot-toast";
import { useNavigate } from "react-router-dom";
import { uploadDocument, listDocuments, deleteDocument } from "../lib/api";
import { PageHeader } from "../components/PageHeader";
import { formatBytes } from "../lib/utils";

export function Upload() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadState, setUploadState] = useState<"idle" | "uploading" | "analyzing" | "success" | "error">("idle");
  const [errorMsg, setErrorMsg] = useState("");

  const { data: docsData, isLoading: isDocsLoading } = useQuery({
    queryKey: ["documents"],
    queryFn: () => listDocuments().then((r) => r.data),
  });
  const docs = docsData || [];

  const uploadMut = useMutation({
    mutationFn: (file: File) => {
      setUploadState("uploading");
      setUploadProgress(10);
      const iv = setInterval(() => {
        setUploadProgress((prev) => {
          if (prev >= 85) { clearInterval(iv); setUploadState("analyzing"); return 85; }
          return prev + 10;
        });
      }, 300);
      return uploadDocument(file)
        .then((res) => { clearInterval(iv); setUploadProgress(100); return res.data; })
        .catch((err) => { clearInterval(iv); throw err; });
    },
    onSuccess: (data) => {
      setUploadState("success");
      toast.success("Document uploaded and analyzed successfully!");
      queryClient.invalidateQueries({ queryKey: ["documents"] });
      setTimeout(() => navigate("/analysis", { state: { docId: data.id } }), 1500);
    },
    onError: (error: any) => {
      setUploadState("error");
      const msg = error.message || "Upload failed";
      setErrorMsg(msg);
      toast.error(msg);
    },
  });

  const deleteMut = useMutation({
    mutationFn: (id: number) => deleteDocument(id),
    onSuccess: () => { toast.success("Document deleted"); queryClient.invalidateQueries({ queryKey: ["documents"] }); },
    onError: (err: any) => toast.error(err.message || "Delete failed"),
  });

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop: (accepted, rejected) => {
      if (rejected.length > 0) {
        const code = rejected[0].errors[0]?.code;
        const msg = code === "file-too-large"
          ? "File exceeds 500 MB limit."
          : code === "file-invalid-type"
          ? "Invalid file type. Use TXT, PDF, or DOCX."
          : "File rejected.";
        setErrorMsg(msg);
        setUploadState("error");
        toast.error(msg);
        return;
      }
      if (accepted.length > 0) uploadMut.mutate(accepted[0]);
    },
    maxFiles: 1,
    maxSize: 500 * 1024 * 1024,
    accept: {
      "text/plain": [".txt"],
      "application/pdf": [".pdf"],
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
    },
  });

  const resetUpload = () => { setUploadState("idle"); setUploadProgress(0); setErrorMsg(""); };

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <PageHeader
        title="Upload Document"
        subtitle="Upload TXT, PDF, or DOCX — up to 500 MB — for deep AI analysis"
        icon={<UploadIcon size={22} />}
      />

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mt-6">
        {/* Drop zone */}
        <div className="md:col-span-2">
          <div className="glass-card p-6 min-h-[340px] flex flex-col justify-center items-center overflow-hidden">
            <AnimatePresence mode="wait">

              {uploadState === "idle" && (
                <motion.div
                  key="idle"
                  initial={{ opacity: 0, scale: 0.97 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.97 }}
                  className="w-full h-full"
                >
                  <div
                    {...getRootProps()}
                    className="w-full h-full flex flex-col items-center justify-center cursor-pointer p-8"
                  >
                  <input {...getInputProps()} />
                  <div className={`w-20 h-20 rounded-full flex items-center justify-center mb-6 transition-all duration-300 ${
                    isDragActive ? "bg-brand-500/20 text-brand-400 scale-110" : "bg-white/5 text-slate-400 hover:bg-white/10 hover:text-white"
                  }`}>
                    <UploadIcon size={36} className={isDragActive ? "animate-bounce" : ""} />
                  </div>
                  <h3 className="text-lg font-semibold text-white mb-2">
                    {isDragActive ? "Drop the file here" : "Drag & drop your file here"}
                  </h3>
                  <p className="text-slate-400 text-sm text-center mb-4 max-w-md">
                    Or click to browse. Supports <strong className="text-brand-400">PDF</strong>,{" "}
                    <strong className="text-brand-400">DOCX</strong>, and{" "}
                    <strong className="text-brand-400">TXT</strong> — up to 500 MB.
                  </p>
                  <div className="flex gap-3 text-xs text-slate-500 border border-white/5 bg-white/5 rounded-full px-4 py-1.5">
                    <span>TXT</span><span>•</span><span>PDF</span><span>•</span><span>DOCX</span>
                  </div>
                  </div>
                </motion.div>
              )}

              {(uploadState === "uploading" || uploadState === "analyzing") && (
                <motion.div
                  key="loading"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  className="flex flex-col items-center justify-center p-8 w-full"
                >
                  <div className="w-16 h-16 rounded-full border-4 border-brand-500/30 border-t-brand-500 animate-spin mb-6" />
                  <h3 className="text-lg font-semibold text-white mb-1">
                    {uploadState === "uploading" ? "Uploading…" : "Running AI Analysis…"}
                  </h3>
                  <p className="text-slate-400 text-sm text-center mb-6 max-w-md">
                    {uploadState === "uploading"
                      ? "Sending file to LexiMind Core…"
                      : "Tokenizing, extracting entities, running NLP pipelines…"}
                  </p>
                  <div className="w-full max-w-md bg-white/5 h-2 rounded-full overflow-hidden">
                    <motion.div
                      className="bg-gradient-to-r from-brand-500 to-purple-500 h-full rounded-full"
                      initial={{ width: "0%" }}
                      animate={{ width: `${uploadProgress}%` }}
                      transition={{ duration: 0.2 }}
                    />
                  </div>
                  <span className="text-xs text-brand-400 font-semibold mt-2">{uploadProgress}%</span>
                </motion.div>
              )}

              {uploadState === "success" && (
                <motion.div
                  key="success"
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0 }}
                  className="flex flex-col items-center justify-center p-8 text-center"
                >
                  <div className="w-16 h-16 bg-emerald-500/10 text-emerald-400 rounded-full flex items-center justify-center mb-6">
                    <CheckCircle2 size={36} />
                  </div>
                  <h3 className="text-lg font-semibold text-white mb-1">Upload Complete!</h3>
                  <p className="text-slate-400 text-sm mb-6">Redirecting to analysis dashboard…</p>
                  <div className="flex items-center gap-2 text-brand-400 text-sm font-semibold animate-pulse">
                    Loading <ArrowRight size={14} />
                  </div>
                </motion.div>
              )}

              {uploadState === "error" && (
                <motion.div
                  key="error"
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0 }}
                  className="flex flex-col items-center justify-center p-8 text-center"
                >
                  <div className="w-16 h-16 bg-red-500/10 text-red-400 rounded-full flex items-center justify-center mb-6">
                    <AlertCircle size={36} />
                  </div>
                  <h3 className="text-lg font-semibold text-white mb-1">Upload Failed</h3>
                  <p className="text-red-400 text-sm mb-6 bg-red-500/5 border border-red-500/10 p-3 rounded-xl max-w-md">
                    {errorMsg}
                  </p>
                  <button onClick={resetUpload} className="btn-primary">Try Another File</button>
                </motion.div>
              )}

            </AnimatePresence>
          </div>
        </div>

        {/* Recent uploads */}
        <div className="space-y-4">
          <h3 className="section-title">Recent Documents</h3>
          {isDocsLoading ? (
            <div className="space-y-3">
              {[1, 2, 3].map((n) => <div key={n} className="glass-card p-4 h-20 animate-pulse bg-white/5" />)}
            </div>
          ) : docs.length === 0 ? (
            <div className="glass-card p-8 text-center text-slate-500 text-sm">No documents yet.</div>
          ) : (
            <div className="space-y-3 max-h-[360px] overflow-y-auto pr-1">
              {docs.map((doc: any) => (
                <div key={doc.id} className="glass-card p-4 flex items-center justify-between gap-3 group hover:bg-white/10 transition-all">
                  <div className="flex items-center gap-3 overflow-hidden">
                    <div className="w-9 h-9 rounded-xl bg-white/5 text-slate-400 flex items-center justify-center shrink-0">
                      <FileText size={16} />
                    </div>
                    <div className="overflow-hidden">
                      <p className="font-medium text-white text-xs truncate">{doc.original_filename}</p>
                      <p className="text-[10px] text-slate-400 mt-0.5">
                        {formatBytes(doc.file_size)} • {doc.word_count?.toLocaleString()} words
                      </p>
                    </div>
                  </div>
                  <button
                    onClick={() => deleteMut.mutate(doc.id)}
                    disabled={deleteMut.isPending}
                    className="p-1.5 text-slate-500 hover:text-red-400 hover:bg-red-500/10 rounded-lg shrink-0 opacity-0 group-hover:opacity-100 transition-all"
                  >
                    <Trash2 size={13} />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
