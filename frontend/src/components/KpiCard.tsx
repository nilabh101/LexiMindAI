import { motion } from "framer-motion";
import { ReactNode } from "react";
import { cn } from "../lib/utils";

interface Props {
  label: string;
  value: string | number;
  icon?: ReactNode;
  sub?: string;
  color?: string;
  delay?: number;
}

export function KpiCard({ label, value, icon, sub, color = "brand", delay = 0 }: Props) {
  const colorMap: Record<string, string> = {
    brand: "text-brand-400",
    green: "text-emerald-400",
    yellow: "text-amber-400",
    red: "text-red-400",
    purple: "text-purple-400",
    blue: "text-sky-400",
    pink: "text-pink-400",
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay, duration: 0.35 }}
      className="kpi-card"
    >
      <div className="flex items-start justify-between">
        <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">{label}</span>
        {icon && (
          <span className={cn("opacity-70", colorMap[color] || colorMap.brand)}>{icon}</span>
        )}
      </div>
      <div className={cn("text-2xl font-bold mt-1", colorMap[color] || colorMap.brand)}>
        {value}
      </div>
      {sub && <div className="text-xs text-slate-500 mt-0.5">{sub}</div>}
    </motion.div>
  );
}
