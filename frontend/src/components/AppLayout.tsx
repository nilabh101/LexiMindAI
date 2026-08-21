import { NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import {
  Brain, LayoutDashboard, BookOpen, Layers, Map, Zap,
  FileText, StickyNote, Library, MessageCircle, TrendingUp,
  User, LogOut, Menu, X, Search
} from "lucide-react";
import { useState } from "react";
import { cn } from "../lib/utils";
import { loadUser, clearUser } from "../store/userStore";
import { ChatBot } from "./ChatBot";

const NAV_ITEMS = [
  { to: "/app",               icon: LayoutDashboard, label: "Dashboard",    end: true },
  { to: "/app/learn",         icon: BookOpen,        label: "Learn"               },
  { to: "/app/subjects",      icon: Layers,          label: "Subjects"            },
  { to: "/app/learning-path", icon: Map,             label: "Learning Path"       },
  { to: "/app/quizzes",       icon: Zap,             label: "Quizzes"             },
  { to: "/app/pyqs",          icon: FileText,        label: "PYQs"                },
  { to: "/app/notes",         icon: StickyNote,      label: "Notes"               },
  { to: "/app/library",       icon: Library,         label: "My Library"          },
  { to: "/app/tutor",         icon: MessageCircle,   label: "AI Tutor"            },
  { to: "/app/progress",      icon: TrendingUp,      label: "Progress"            },
];

export function AppLayout() {
  const location = useLocation();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [query, setQuery] = useState("");
  const user = loadUser();

  const submitSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    navigate(`/app/search?q=${encodeURIComponent(query.trim())}`);
    setSidebarOpen(false);
  };

  const handleLogout = () => { clearUser(); navigate("/"); };

  const SidebarContent = () => (
    <div className="flex flex-col h-full">
      {/* Logo */}
      <div className="px-5 py-5 border-b border-white/6">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shrink-0">
            <Brain size={16} className="text-white" />
          </div>
          <div>
            <div className="font-bold text-white text-sm leading-tight">LexiMind AI</div>
            <div className="text-[10px] text-indigo-400 leading-tight">Adaptive Learning</div>
          </div>
        </div>
      </div>

      {/* User info */}
      {user && (
        <div className="px-4 py-3 mx-3 mt-3 rounded-xl bg-white/3 border border-white/6">
          <div className="font-semibold text-white text-sm truncate">{user.name}</div>
          <div className="text-[10px] text-slate-500 mt-0.5 truncate">
            {user.academicProfile?.courseId
              ? user.academicProfile.courseId.replace(/-/g, " ").replace(/\b\w/g, c => c.toUpperCase())
              : "Student"}
          </div>
        </div>
      )}

      {/* Search */}
      <form onSubmit={submitSearch} className="px-3 mt-3">
        <div className="flex items-center gap-2 bg-white/5 border border-white/8 rounded-xl px-3">
          <Search size={14} className="text-slate-500 shrink-0" />
          <input
            value={query}
            onChange={e => setQuery(e.target.value)}
            placeholder="Search"
            aria-label="Search"
            className="flex-1 bg-transparent py-2 text-sm text-white placeholder-slate-500 outline-none min-w-0"
          />
        </div>
      </form>

      {/* Nav */}
      <nav className="flex-1 px-3 py-3 space-y-0.5 overflow-y-auto">
        {NAV_ITEMS.map(({ to, icon: Icon, label, end }, i) => (
          <NavLink key={to} to={to} end={end}
            className={({ isActive }) => cn(
              "flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-150",
              isActive
                ? "bg-indigo-600/25 text-indigo-300 shadow-sm shadow-indigo-500/10"
                : "text-slate-400 hover:text-slate-200 hover:bg-white/5"
            )}
            onClick={() => setSidebarOpen(false)}
          >
            <Icon size={16} />
            {label}
          </NavLink>
        ))}
      </nav>

      {/* Footer */}
      <div className="px-3 pb-4 space-y-0.5 border-t border-white/6 pt-3">
        <NavLink to="/app/profile"
          className={({ isActive }) => cn(
            "flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all",
            isActive ? "bg-indigo-600/25 text-indigo-300" : "text-slate-400 hover:text-slate-200 hover:bg-white/5"
          )}>
          <User size={16} /> Profile
        </NavLink>
        <button onClick={handleLogout}
          className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium text-slate-500 hover:text-slate-300 hover:bg-white/5 transition-all">
          <LogOut size={16} /> Sign Out
        </button>
      </div>
    </div>
  );

  return (
    <div className="flex h-screen overflow-hidden bg-[#0a0a14]">
      {/* Desktop sidebar */}
      <aside className="hidden lg:flex w-60 shrink-0 flex-col border-r border-white/6 bg-[#0d0d1a]">
        {SidebarContent()}
      </aside>

      {/* Mobile sidebar overlay */}
      {sidebarOpen && (
        <div className="lg:hidden fixed inset-0 z-50 flex">
          <div className="absolute inset-0 bg-black/60" onClick={() => setSidebarOpen(false)} />
          <motion.div initial={{ x: -240 }} animate={{ x: 0 }} exit={{ x: -240 }}
            className="relative w-60 bg-[#0d0d1a] border-r border-white/6 h-full z-10">
            <button onClick={() => setSidebarOpen(false)} className="absolute top-4 right-4 text-slate-400 hover:text-white">
              <X size={18} />
            </button>
            {SidebarContent()}
          </motion.div>
        </div>
      )}

      {/* Main */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Mobile top bar */}
        <div className="lg:hidden flex items-center gap-3 px-4 py-3 border-b border-white/6 bg-[#0d0d1a]">
          <button onClick={() => setSidebarOpen(true)} className="text-slate-400 hover:text-white">
            <Menu size={20} />
          </button>
          <div className="flex items-center gap-2">
            <Brain size={16} className="text-indigo-400" />
            <span className="font-bold text-white text-sm">LexiMind AI</span>
          </div>
        </div>

        {/* Page content */}
        <main className="flex-1 overflow-y-auto">
          <motion.div key={location.pathname} initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.2 }} className="min-h-full">
            <Outlet />
          </motion.div>
        </main>
      </div>

      {/* AI Tutor floating button */}
      <ChatBot />
    </div>
  );
}
