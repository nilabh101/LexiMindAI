import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { Brain, Mail, Lock, User, ArrowRight } from "lucide-react";
import { saveUser, useDemoUser } from "../../store/userStore";

export function RegisterPage() {
  const navigate = useNavigate();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const handleRegister = (e: React.FormEvent) => {
    e.preventDefault();
    // Phase 1: create a local user then go to onboarding
    const base = useDemoUser();
    saveUser({ ...base, id: `user-${Date.now()}`, name: name || "Student", email, onboardingComplete: false, streak: 0 });
    navigate("/onboarding");
  };

  return (
    <div className="min-h-screen bg-[#0a0a14] flex items-center justify-center p-4">
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="w-full max-w-md">
        <div className="flex items-center gap-2.5 mb-10 justify-center">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
            <Brain size={18} className="text-white" />
          </div>
          <span className="font-bold text-white text-xl">LexiMind AI</span>
        </div>

        <div className="bg-white/3 border border-white/8 rounded-3xl p-8">
          <h1 className="text-2xl font-bold text-white mb-1">Create your account</h1>
          <p className="text-slate-400 text-sm mb-8">Start your personalized learning journey</p>

          <form onSubmit={handleRegister} className="space-y-4">
            <div>
              <label className="text-xs text-slate-400 mb-1.5 block">Full name</label>
              <div className="relative">
                <User size={15} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500" />
                <input type="text" value={name} onChange={e => setName(e.target.value)} placeholder="Your name" required
                  className="w-full bg-white/5 border border-white/10 rounded-xl pl-10 pr-4 py-3 text-sm text-white placeholder-slate-500 outline-none focus:border-indigo-500/60 focus:ring-2 focus:ring-indigo-500/20 transition-all" />
              </div>
            </div>
            <div>
              <label className="text-xs text-slate-400 mb-1.5 block">Email address</label>
              <div className="relative">
                <Mail size={15} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500" />
                <input type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="you@example.com" required
                  className="w-full bg-white/5 border border-white/10 rounded-xl pl-10 pr-4 py-3 text-sm text-white placeholder-slate-500 outline-none focus:border-indigo-500/60 focus:ring-2 focus:ring-indigo-500/20 transition-all" />
              </div>
            </div>
            <div>
              <label className="text-xs text-slate-400 mb-1.5 block">Password</label>
              <div className="relative">
                <Lock size={15} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500" />
                <input type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="Create a password" required
                  className="w-full bg-white/5 border border-white/10 rounded-xl pl-10 pr-4 py-3 text-sm text-white placeholder-slate-500 outline-none focus:border-indigo-500/60 focus:ring-2 focus:ring-indigo-500/20 transition-all" />
              </div>
            </div>
            <button type="submit"
              className="w-full bg-indigo-600 hover:bg-indigo-500 text-white py-3 rounded-xl font-semibold text-sm flex items-center justify-center gap-2 transition-all shadow-lg shadow-indigo-500/20 mt-2">
              Create Account <ArrowRight size={15} />
            </button>
          </form>

          <p className="text-center text-slate-500 text-xs mt-6">
            Already have an account?{" "}
            <Link to="/login" className="text-indigo-400 hover:text-indigo-300">Sign in</Link>
          </p>
        </div>
      </motion.div>
    </div>
  );
}
