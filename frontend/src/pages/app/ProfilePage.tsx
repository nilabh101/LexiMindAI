import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { User, LogOut, BookOpen, Target, Clock } from "lucide-react";
import { loadUser, clearUser, saveUser } from "../../store/userStore";
import { DEMO_USER } from "../../data/demoData";
import { getCourse } from "../../data/curriculum";

const GOAL_LABELS: Record<string, string> = {
  score_higher: "Score Higher", pass_exams: "Pass Exams",
  master_concepts: "Master Concepts", complete_syllabus: "Complete Syllabus",
  practice_pyqs: "Practice PYQs", competitive_exam: "Competitive Exam",
};

export function ProfilePage() {
  const navigate = useNavigate();
  const user = loadUser() ?? DEMO_USER;
  const [name, setName] = useState(user.name);
  const course = getCourse(user.academicProfile?.courseId ?? "");

  const save = () => { saveUser({ ...user, name }); };
  const logout = () => { clearUser(); navigate("/"); };

  return (
    <div className="p-6 lg:p-8 max-w-2xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white">Profile & Settings</h1>
      </div>

      <div className="space-y-5">
        {/* Avatar + name */}
        <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="bg-white/3 border border-white/6 rounded-2xl p-6">
          <div className="flex items-center gap-4 mb-5">
            <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-2xl font-bold text-white">
              {user.name[0]}
            </div>
            <div>
              <div className="font-bold text-white text-lg">{user.name}</div>
              <div className="text-slate-400 text-sm">{user.email || "No email set"}</div>
            </div>
          </div>
          <label className="text-xs text-slate-400 mb-1.5 block">Display Name</label>
          <div className="flex gap-3">
            <input value={name} onChange={e => setName(e.target.value)}
              className="flex-1 bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white placeholder-slate-500 outline-none focus:border-indigo-500/50 transition-all" />
            <button onClick={save} className="bg-indigo-600 hover:bg-indigo-500 text-white px-5 py-2.5 rounded-xl text-sm font-medium transition-all">Save</button>
          </div>
        </motion.div>

        {/* Academic profile */}
        <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.05 }} className="bg-white/3 border border-white/6 rounded-2xl p-6">
          <h3 className="font-semibold text-white mb-4 flex items-center gap-2"><BookOpen size={16} className="text-indigo-400" /> Academic Profile</h3>
          <div className="space-y-3 text-sm">
            <div className="flex items-center justify-between py-2.5 border-b border-white/6">
              <span className="text-slate-400">Education Level</span>
              <span className="text-white capitalize">{user.academicProfile?.educationLevel ?? "—"}</span>
            </div>
            <div className="flex items-center justify-between py-2.5 border-b border-white/6">
              <span className="text-slate-400">Course</span>
              <span className="text-white">{course?.name ?? user.academicProfile?.courseId ?? "—"}</span>
            </div>
            <div className="flex items-center justify-between py-2.5 border-b border-white/6">
              <span className="text-slate-400">Year</span>
              <span className="text-white">{user.academicProfile?.educationLevel === "school" ? `Class ${user.academicProfile.year}` : `Year ${user.academicProfile?.year}`}</span>
            </div>
            <div className="flex items-center justify-between py-2.5">
              <span className="text-slate-400">Subjects</span>
              <span className="text-white">{user.academicProfile?.subjectIds.length ?? 0} selected</span>
            </div>
          </div>
          <button onClick={() => navigate("/onboarding")} className="mt-4 text-sm text-indigo-400 hover:text-indigo-300 transition-colors">Update academic profile →</button>
        </motion.div>

        {/* Goals */}
        <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="bg-white/3 border border-white/6 rounded-2xl p-6">
          <h3 className="font-semibold text-white mb-4 flex items-center gap-2"><Target size={16} className="text-emerald-400" /> Learning Goals</h3>
          <div className="flex items-center justify-between text-sm py-2.5 border-b border-white/6">
            <span className="text-slate-400">Study Goal</span>
            <span className="text-white">{GOAL_LABELS[user.studyGoal] ?? user.studyGoal}</span>
          </div>
          <div className="flex items-center justify-between text-sm py-2.5">
            <span className="text-slate-400">Daily Target</span>
            <span className="text-white flex items-center gap-1.5"><Clock size={13} />{user.dailyStudyMinutes} min / day</span>
          </div>
        </motion.div>

        {/* Logout */}
        <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.15 }}>
          <button onClick={logout} className="w-full flex items-center justify-center gap-2 py-3.5 rounded-2xl border border-red-500/20 bg-red-500/5 text-red-400 hover:bg-red-500/10 transition-all text-sm font-medium">
            <LogOut size={15} /> Sign Out
          </button>
        </motion.div>
      </div>
    </div>
  );
}
