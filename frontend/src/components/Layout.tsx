import { NavLink, Outlet, useLocation } from "react-router-dom";
import { motion } from "framer-motion";
import {
  Brain, Upload, BarChart3, MessageSquare, BookOpen,
  GitCompare, TrendingUp, FileText, Layers, Zap, Home
} from "lucide-react";
import { cn } from "../lib/utils";

const NAV = [
  { to: "/", icon: Home, label: "Dashboard" },
  { to: "/upload", icon: Upload, label: "Upload" },
  { to: "/words", icon: BarChart3, label: "Word Analysis" },
  { to: "/sentiment", icon: MessageSquare, label: "Sentiment" },
  { to: "/topics", icon: Layers, label: "Topics & Entities" },
  { to: "/dna", icon: Brain, label: "Document DNA" },
  { to: "/summary", icon: BookOpen, label: "AI Summary" },
  { to: "/quiz", icon: Zap, label: "Quiz & Questions" },
  { to: "/compare", icon: GitCompare, label: "Compare" },
  { to: "/trends", icon: TrendingUp, label: "Trends" },
  { to: "/reports", icon: FileText, label: "Reports" },
  { to: "/presentation", icon: Brain, label: "IIT Presentation" },
];

export function Layout() {
  const location = useLocation();
  return (
    <div className="flex h-screen overflow-hidden">
      {/* Sidebar */}
      <aside className="w-60 glass border-r border-white/10 flex flex-col shrink-0 overflow-y-auto">
        {/* Logo */}
        <div className="p-5 border-b border-white/10">
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="flex items-center gap-3"
          >
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-brand-500 to-purple-500 flex items-center justify-center shadow-lg shadow-brand-500/30">
              <Brain size={18} className="text-white" />
            </div>
            <div>
              <div className="font-bold text-white text-sm leading-tight">LexiMind AI</div>
              <div className="text-[10px] text-brand-400 leading-tight">Document Intelligence</div>
            </div>
          </motion.div>
        </div>

        {/* Nav */}
        <nav className="flex-1 p-3 space-y-0.5">
          {NAV.map(({ to, icon: Icon, label }, i) => (
            <motion.div
              key={to}
              initial={{ opacity: 0, x: -16 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.04 }}
            >
              <NavLink
                to={to}
                end={to === "/"}
                className={({ isActive }) =>
                  cn(
                    "flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-200",
                    isActive
                      ? "bg-brand-600/30 text-brand-300 shadow-sm shadow-brand-500/20"
                      : "text-slate-400 hover:text-slate-200 hover:bg-white/5"
                  )
                }
              >
                <Icon size={16} />
                {label}
              </NavLink>
            </motion.div>
          ))}
        </nav>

        {/* Footer */}
        <div className="p-4 border-t border-white/10">
          <div className="text-[11px] text-slate-500 text-center">
            LexiMind AI v1.0.0<br />
            <span className="text-brand-500">IIT Project 2026</span>
          </div>
        </div>
      </aside>

      {/* Main */}
      <main className="flex-1 overflow-y-auto">
        <motion.div
          key={location.pathname}
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.25 }}
          className="min-h-full"
        >
          <Outlet />
        </motion.div>
      </main>
    </div>
  );
}
