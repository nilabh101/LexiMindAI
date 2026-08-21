import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import {
  BookOpen, Zap, FileText, MessageCircle, ArrowRight,
  Flame, Target, Clock, CheckCircle, AlertCircle, BarChart3
} from "lucide-react";
import { loadUser } from "../../store/userStore";
import { DEMO_MASTERY, DEMO_RECENT_SESSIONS, DEMO_USER } from "../../data/demoData";
import { CONCEPTS, getSubject } from "../../data/curriculum";
import { masteryColor, getWeakConcepts, getLearningPath } from "../../services/adaptiveEngine";

function greeting() {
  const h = new Date().getHours();
  if (h < 12) return "Good morning";
  if (h < 17) return "Good afternoon";
  return "Good evening";
}

function StatCard({ label, value, sub, color, icon: Icon }: any) {
  return (
    <div className="bg-white/3 border border-white/6 rounded-2xl p-5">
      <div className={`${color} mb-3`}><Icon size={18} /></div>
      <div className={`text-2xl font-bold text-white`}>{value}</div>
      {sub && <div className="text-xs text-slate-500 mt-0.5">{sub}</div>}
      <div className="text-xs text-slate-400 mt-1">{label}</div>
    </div>
  );
}

export function AppDashboard() {
  const user = loadUser() ?? DEMO_USER;
  const learningPath = getLearningPath();
  const currentFocus = learningPath.find(i => i.isCurrentFocus);
  const currentConcept = currentFocus ? CONCEPTS.find(c => c.id === currentFocus.conceptId) : null;
  const currentSubject = currentConcept ? getSubject(currentConcept.subjectId) : null;

  const weakConcepts = getWeakConcepts();
  const mastered = DEMO_MASTERY.filter(m => m.status === "mastered").length;
  const inProgress = DEMO_MASTERY.filter(m => m.status === "in_progress").length;

  const todayPlan = [
    { label: `Review ${currentConcept?.name ?? "your current concept"}`, done: false, type: "study" },
    { label: "Practice 5 questions", done: false, type: "quiz" },
    { label: `Complete ${currentConcept?.name ?? ""} quiz`, done: false, type: "quiz" },
    { label: "Review mistakes from last session", done: true, type: "review" },
  ];

  return (
    <div className="p-6 lg:p-8 max-w-6xl mx-auto">
      {/* Header */}
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="mb-8">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-bold text-white">
              {greeting()}, {user.name.split(" ")[0]} 👋
            </h1>
            <p className="text-slate-400 text-sm mt-1">
              You're on a <span className="text-amber-400 font-semibold">{user.streak}-day streak</span> — keep it going!
            </p>
          </div>
          <div className="flex items-center gap-2 bg-amber-500/10 border border-amber-500/20 px-3 py-2 rounded-xl">
            <Flame size={16} className="text-amber-400" />
            <span className="text-amber-300 font-bold text-sm">{user.streak}</span>
          </div>
        </div>
      </motion.div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <StatCard label="Concepts Mastered" value={mastered} sub={`of ${DEMO_MASTERY.length} total`} color="text-emerald-400" icon={CheckCircle} />
        <StatCard label="In Progress" value={inProgress} color="text-amber-400" icon={Target} />
        <StatCard label="Study Time" value="340 min" sub="this week" color="text-indigo-400" icon={Clock} />
        <StatCard label="Quizzes Taken" value="12" color="text-purple-400" icon={BarChart3} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        {/* Continue Learning */}
        <div className="lg:col-span-2">
          <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-3">Continue Learning</h2>
          {currentConcept ? (
            <Link to={`/app/concepts/${currentConcept.id}`}>
              <div className="bg-gradient-to-br from-indigo-600/20 to-purple-600/10 border border-indigo-500/20 rounded-2xl p-6 hover:border-indigo-500/40 transition-all group">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <div className="w-12 h-12 rounded-xl bg-indigo-600/30 flex items-center justify-center text-2xl">
                      {currentSubject?.icon ?? "📚"}
                    </div>
                    <div>
                      <div className="font-semibold text-white text-lg">{currentConcept.name}</div>
                      <div className="text-sm text-slate-400">{currentSubject?.name}</div>
                    </div>
                  </div>
                  <span className="text-xs bg-amber-500/20 text-amber-300 border border-amber-500/20 px-2.5 py-1 rounded-lg">In Progress</span>
                </div>
                <p className="text-slate-400 text-sm mb-4 line-clamp-2">{currentConcept.description}</p>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 text-xs text-slate-500">
                    <Clock size={12} /> {currentConcept.estimatedMinutes} min
                  </div>
                  <div className="flex items-center gap-1 text-indigo-400 text-sm font-medium group-hover:gap-2 transition-all">
                    Continue <ArrowRight size={14} />
                  </div>
                </div>
                {/* Mastery bar */}
                <div className="mt-4 bg-white/5 rounded-full h-1.5">
                  <div className="bg-indigo-500 h-1.5 rounded-full w-[30%]" />
                </div>
                <div className="text-xs text-slate-500 mt-1">30% mastery</div>
              </div>
            </Link>
          ) : (
            <div className="bg-white/3 border border-white/6 rounded-2xl p-8 text-center">
              <BookOpen size={32} className="text-slate-600 mx-auto mb-3" />
              <p className="text-slate-400">No active concept. Start from Subjects.</p>
              <Link to="/app/subjects" className="inline-flex items-center gap-1 text-indigo-400 text-sm mt-3 hover:gap-2 transition-all">Browse Subjects <ArrowRight size={13} /></Link>
            </div>
          )}
        </div>

        {/* Today's Plan */}
        <div>
          <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-3">Today's Plan</h2>
          <div className="bg-white/3 border border-white/6 rounded-2xl p-5 space-y-3">
            {todayPlan.map((item, i) => (
              <div key={i} className="flex items-start gap-3">
                <div className={`mt-0.5 w-5 h-5 rounded-full border flex items-center justify-center shrink-0 ${item.done ? "bg-emerald-500/20 border-emerald-500/50" : "border-white/15"}`}>
                  {item.done && <CheckCircle size={11} className="text-emerald-400" />}
                </div>
                <span className={`text-sm leading-snug ${item.done ? "line-through text-slate-500" : "text-slate-300"}`}>{item.label}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Weak areas + Recent activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* Weak Areas */}
        <div>
          <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-3">Needs Attention</h2>
          <div className="space-y-2">
            {weakConcepts.length === 0 ? (
              <div className="bg-white/3 border border-white/6 rounded-xl p-4 text-center text-slate-500 text-sm">All good! No weak areas.</div>
            ) : weakConcepts.map((m, i) => {
              const concept = CONCEPTS.find(c => c.id === m.conceptId);
              const sub = concept ? getSubject(concept.subjectId) : null;
              if (!concept) return null;
              return (
                <Link key={i} to={`/app/concepts/${m.conceptId}`}>
                  <div className="bg-white/3 border border-white/6 rounded-xl p-4 flex items-center justify-between hover:bg-white/5 transition-all">
                    <div>
                      <div className="text-sm font-medium text-white">{concept.name}</div>
                      <div className="text-xs text-slate-500 mt-0.5">{sub?.name}</div>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className={`text-sm font-bold ${masteryColor(m.score)}`}>{m.score}%</span>
                      <AlertCircle size={14} className="text-amber-400" />
                    </div>
                  </div>
                </Link>
              );
            })}
          </div>
        </div>

        {/* Recent Activity */}
        <div>
          <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-3">Recent Activity</h2>
          <div className="space-y-2">
            {DEMO_RECENT_SESSIONS.map((s, i) => {
              const concept = s.conceptId ? CONCEPTS.find(c => c.id === s.conceptId) : null;
              const sub = getSubject(s.subjectId ?? "");
              const typeIcon = s.type === "quiz" ? "⚡" : s.type === "pyq" ? "📝" : "📖";
              const typeColor = s.type === "quiz" ? "text-amber-400" : s.type === "pyq" ? "text-blue-400" : "text-indigo-400";
              return (
                <div key={i} className="bg-white/3 border border-white/6 rounded-xl p-4 flex items-center gap-3">
                  <span className="text-lg">{typeIcon}</span>
                  <div className="flex-1">
                    <div className="text-sm font-medium text-white">{concept?.name ?? sub?.name ?? "Study Session"}</div>
                    <div className="text-xs text-slate-500 mt-0.5">{sub?.name} · {s.durationMinutes} min</div>
                  </div>
                  <span className={`text-xs font-medium capitalize ${typeColor}`}>{s.type}</span>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div>
        <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-3">Quick Actions</h2>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {[
            { to: "/app/notes",         icon: BookOpen,       label: "Study Notes",   color: "from-indigo-500 to-purple-500" },
            { to: "/app/quizzes",       icon: Zap,            label: "Take Quiz",     color: "from-amber-500 to-orange-500" },
            { to: "/app/pyqs",          icon: FileText,       label: "Practice PYQs", color: "from-blue-500 to-cyan-500"   },
            { to: "/app/tutor",         icon: MessageCircle,  label: "Ask AI Tutor",  color: "from-emerald-500 to-teal-500"},
          ].map(({ to, icon: Icon, label, color }) => (
            <Link key={to} to={to}
              className="bg-white/3 border border-white/6 rounded-2xl p-5 hover:bg-white/5 transition-all group text-center">
              <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${color} flex items-center justify-center mx-auto mb-3`}>
                <Icon size={18} className="text-white" />
              </div>
              <div className="text-sm font-medium text-slate-300 group-hover:text-white transition-colors">{label}</div>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}
