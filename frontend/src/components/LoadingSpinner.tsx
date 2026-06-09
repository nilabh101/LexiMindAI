import { motion } from "framer-motion";

export function LoadingSpinner({ text = "Analyzing…" }: { text?: string }) {
  return (
    <div className="flex flex-col items-center justify-center gap-4 py-16">
      <div className="relative w-14 h-14">
        <motion.div
          className="absolute inset-0 rounded-full border-2 border-brand-500/30"
          animate={{ rotate: 360 }}
          transition={{ duration: 1.5, repeat: Infinity, ease: "linear" }}
          style={{ borderTopColor: "#6366f1" }}
        />
        <motion.div
          className="absolute inset-2 rounded-full border-2 border-purple-500/30"
          animate={{ rotate: -360 }}
          transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
          style={{ borderTopColor: "#a855f7" }}
        />
      </div>
      <p className="text-slate-400 text-sm animate-pulse">{text}</p>
    </div>
  );
}
