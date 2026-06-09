import { useState } from "react";
import { useDropzone } from "react-dropzone";
import { motion, AnimatePresence } from "framer-motion";
import { Upload as UploadIcon, FileText, CheckCircle2, AlertCircle, Trash2, ArrowRight } from "lucide-react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "react-hot-toast";
import { useNavigate } from "react-router-dom";
import { uploadDocument, listDocuments, deleteDocument } from "../lib/api";
import { PageHeader } from "../components/PageHeader";
import { formatBytes, formatDate } from "../lib/utils";

export function Upload() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [uploadProgress, setUploadProgress] = useState<number>(0);
  const [uploadState, setUploadState] = useState<"idle" | "uploading" | "analyzing" | "success" | "error">("idle");
  const [errorMsg, setErrorMsg] = useState<string>("");

  // Get recent uploads
  const { data: docsData, isLoading: isDocsLoading } = useQuery({
    queryKey: ["documents"],
    queryFn: () => listDocuments().then((r) => r.data),
  });

  const docs = docsData || [];

  // Upload mutation
  const uploadMut = useMutation({
    mutationFn: (file: File) => {
      setUploadState("uploading");
      setUploadProgress(10);
      
      // Simulate progress updates for a smoother visual experience
      const progressInterval = setInterval(() => {
        setUploadProgress((prev) => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            setUploadState("analyzing");
            return 90;
          }
          return prev + 15;
        });
      }, 200);

      return uploadDocument(file)
        .then((res) => {
          clearInterval(progressInterval);
          setUploadProgress(100);
          return res.data;
        })
        .catch((err) => {
          clearInterval(progressInterval);
          throw err;
        });
    },
    onSuccess: (data) => {
      setUploadState("success");
      toast.success("Document uploaded and analyzed successfully!");
      queryClient.invalidateQueries({ queryKey: ["documents"] });
      
      // Navigate to Word Analysis for the uploaded document after a brief pause
      setTimeout(() => {
        navigate("/words", { state: { docId: data.id } });
      }, 1500);
    },
    onError: (error: any) => {
      setUploadState("error");
      const message = error.message || "Failed to upload file";
      setErrorMsg(message);
      toast.error(message);
    },
  });

  // Delete mutation
  const deleteMut = useMutation({
    mutationFn: (id: number) => deleteDocument(id),
    onSuccess: () => {
      toast.success("Document deleted");
      queryClient.invalidateQueries({ queryKey: ["documents"] });
    },
    onError: (err: any) => {
      toast.error(err.message || "Failed to delete document");
    },
  });

  const onDrop = (acceptedFiles: File[]) => {
    if (acceptedFiles.length === 0) return;
    const file = acceptedFiles[0];
    uploadMut.mutate(file);
  };

  const { getRootProps, getInputProps, isDragActive, fileRejections } = useDropzone({
    onDrop,
    maxFiles: 1,
    maxSize: 10 * 1024 * 1024, // 10MB
    accept: {
      "text/plain": [".txt"],
      "application/pdf": [".pdf"],
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
    },
  });

  // Triggered when file is rejected by react-dropzone config
  if (fileRejections.length > 0 && uploadState === "idle") {
    const error = fileRejections[0].errors[0];
    let customMsg = "Invalid file.";
    if (error.code === "file-too-large") {
      customMsg = "File is too large. Max size is 10MB.";
    } else if (error.code === "file-invalid-type") {
      customMsg = "Invalid file type. Please upload a TXT, PDF, or DOCX document.";
    }
    setErrorMsg(customMsg);
    setUploadState("error");
    toast.error(customMsg);
  }

  const resetUpload = () => {
    setUploadState("idle");
    setUploadProgress(0);
    setErrorMsg("");
  };

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <PageHeader
        title="Upload Document"
        subtitle="Upload text files, PDFs, or Word documents for deep AI-powered intelligence extraction"
        icon={<UploadIcon size={22} />}
      />

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mt-6">
        {/* Upload Area */}
        <div className="md:col-span-2 space-y-6">
          <div className="glass-card p-6 min-h-[350px] flex flex-col justify-center items-center relative overflow-hidden">
            <AnimatePresence mode="wait">
              {uploadState === "idle" && (
                <div
                  className="w-full h-full flex flex-col items-center justify-center cursor-pointer p-8"
                  {...getRootProps()}
                >
                  <motion.div
                    key="idle"
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0, scale: 0.95 }}
                    className="flex flex-col items-center justify-center w-full h-full"
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
                      Or click to browse from your device. Supports <strong className="text-brand-400">PDF, Word (DOCX)</strong>, and <strong className="text-brand-400">Plain Text (TXT)</strong> files up to 10MB.
                    </p>
                    <div className="flex gap-3 text-xs text-slate-500 border border-white/5 bg-white/5 rounded-full px-4 py-1.5">
                      <span>TXT</span><span>•</span><span>PDF</span><span>•</span><span>DOCX</span>
                    </div>
                  </motion.div>
                </div>
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
                    {uploadState === "uploading" ? "Uploading Document..." : "AI Intelligence Analysis..."}
                  </h3>
                  <p className="text-slate-400 text-sm text-center mb-6 max-w-md">
                    {uploadState === "uploading" 
                      ? "Sending file data securely to LexiMind Core..."
                      : "Running tokenization, entity resolution, emotional indexers, and summary pipelines..."}
                  </p>

                  <div className="w-full max-w-md bg-white/5 h-2 rounded-full overflow-hidden border border-white/5">
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
                  exit={{ opacity: 0, scale: 0.95 }}
                  className="flex flex-col items-center justify-center p-8 text-center"
                >
                  <div className="w-16 h-16 bg-emerald-500/10 text-emerald-400 rounded-full flex items-center justify-center mb-6">
                    <CheckCircle2 size={36} />
                  </div>
                  <h3 className="text-lg font-semibold text-white mb-1">Upload Complete!</h3>
                  <p className="text-slate-400 text-sm mb-6 max-w-sm">
                    Your document was processed successfully. Redirecting you to analysis...
                  </p>
                  <div className="flex items-center gap-2 text-brand-400 text-sm font-semibold animate-pulse">
                    Loading analytics dashboard <ArrowRight size={14} />
                  </div>
                </motion.div>
              )}

              {uploadState === "error" && (
                <motion.div
                  key="error"
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.95 }}
                  className="flex flex-col items-center justify-center p-8 text-center"
                >
                  <div className="w-16 h-16 bg-red-500/10 text-red-400 rounded-full flex items-center justify-center mb-6">
                    <AlertCircle size={36} />
                  </div>
                  <h3 className="text-lg font-semibold text-white mb-1">Analysis Failed</h3>
                  <p className="text-red-400 text-sm mb-6 max-w-md bg-red-500/5 border border-red-500/10 p-3 rounded-xl">
                    {errorMsg}
                  </p>
                  <button onClick={resetUpload} className="btn-primary">
                    Try Another File
                  </button>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>

        {/* Recent Uploads */}
        <div className="space-y-4">
          <h3 className="section-title">Recent Documents</h3>
          {isDocsLoading ? (
            <div className="space-y-3">
              {[1, 2, 3].map((n) => (
                <div key={n} className="glass-card p-4 h-20 animate-pulse bg-white/5" />
              ))}
            </div>
          ) : docs.length === 0 ? (
            <div className="glass-card p-8 text-center text-slate-500 text-sm">
              No documents uploaded yet.
            </div>
          ) : (
            <div className="space-y-3 max-h-[350px] overflow-y-auto pr-1">
              {docs.map((doc: any) => (
                <div
                  key={doc.id}
                  className="glass-card p-4 flex items-center justify-between gap-3 group hover:bg-white/10 transition-all duration-200"
                >
                  <div className="flex items-center gap-3 overflow-hidden">
                    <div className="w-10 h-10 rounded-xl bg-white/5 text-slate-400 flex items-center justify-center shrink-0">
                      <FileText size={18} />
                    </div>
                    <div className="overflow-hidden">
                      <h4 className="font-medium text-white text-xs truncate" title={doc.original_filename}>
                        {doc.original_filename}
                      </h4>
                      <p className="text-[10px] text-slate-400 mt-0.5">
                        {formatBytes(doc.file_size)} • {doc.word_count?.toLocaleString()} words
                      </p>
                    </div>
                  </div>
                  <button
                    onClick={() => deleteMut.mutate(doc.id)}
                    disabled={deleteMut.isPending}
                    className="p-1.5 text-slate-500 hover:text-red-400 hover:bg-red-500/10 rounded-lg shrink-0 opacity-0 group-hover:opacity-100 focus:opacity-100 transition-all duration-200"
                    title="Delete document"
                  >
                    <Trash2 size={14} />
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
