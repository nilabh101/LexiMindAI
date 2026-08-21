import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import {
  Brain, ArrowRight, BookOpen, Zap, Target, TrendingUp,
  CheckCircle, Star, Users, Clock
} from "lucide-react";

const FEATURES = [
  {
    icon: Brain,
    title: "Adaptive Learning",
    desc: "LexiMind understands what you know and dynamically adjusts your learning path. No two students follow the same route.",
    color: "from-indigo-500 to-purple-600",
  },
  {
    icon: BookOpen,
    title: "AI Tutor",
    desc: "Ask questions, get explanations, request examples — all in the context of your exact syllabus and current topic.",
    color: "from-blue-500 to-cyan-500",
  },
  {
    icon: Zap,
    title: "Smart Quizzes",
    desc: "Concept-linked MCQs, fill-in-the-blank, and open questions. Every quiz updates your mastery score in real time.",
    color: "from-amber-500 to-orange-500",
  },
  {
    icon: Target,
    title: "PYQ Practice",
    desc: "Solve previous year questions filtered by subject, chapter, concept, and difficulty level.",
    color: "from-emerald-500 to-teal-500",
  },
  {
    icon: TrendingUp,
    title: "Progress Intelligence",
    desc: "Know exactly which concepts you've mastered and which need more work. Backed by data, not guesswork.",
    color: "from-pink-500 to-rose-500",
  },
  {
    icon: BookOpen,
    title: "Study Library",
    desc: "Upload your notes, textbooks, and PDFs. LexiMind reads them and connects them to your syllabus.",
    color: "from-violet-500 to-purple-500",
  },
];

const STATS = [
  { value: "50+", label: "Subjects covered" },
  { value: "500+", label: "Concepts mapped" },
  { value: "School & College", label: "Class 6 to Final Year" },
];

export function LandingPage() {
  return (
    <div className="min-h-screen bg-[#0a0a14] text-slate-100 font-sans">
      {/* Nav */}
      <nav className="sticky top-0 z-50 border-b border-white/5 bg-[#0a0a14]/90 backdrop-blur-sm">
        <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
              <Brain size={16} className="text-white" />
            </div>
            <span className="font-bold text-white text-lg">LexiMind AI</span>
          </div>
          <div className="flex items-center gap-3">
            <Link to="/login" className="text-slate-400 hover:text-white text-sm px-4 py-2 rounded-lg hover:bg-white/5 transition-all">
              Sign in
            </Link>
            <Link to="/onboarding" className="bg-indigo-600 hover:bg-indigo-500 text-white text-sm px-5 py-2 rounded-xl font-medium transition-all shadow-lg shadow-indigo-500/20">
              Start Learning
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="max-w-6xl mx-auto px-6 pt-24 pb-20 text-center">
        <motion.div initial={{ opacity: 0, y: 24 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }}>
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 text-sm mb-8">
            <Star size={13} /> Adaptive Learning Platform
          </div>
          <h1 className="text-5xl sm:text-6xl font-extrabold text-white leading-tight mb-6">
            Learn smarter.<br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-purple-400">
              Follow your own path.
            </span>
          </h1>
          <p className="text-xl text-slate-400 max-w-2xl mx-auto mb-10 leading-relaxed">
            LexiMind understands what you know, finds what you need to improve,
            and builds a learning path around you — from Class 6 to final year college.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link to="/onboarding"
              className="inline-flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500 text-white px-8 py-4 rounded-2xl font-semibold text-base transition-all shadow-xl shadow-indigo-500/25 hover:shadow-indigo-500/40">
              Start Learning Free <ArrowRight size={18} />
            </Link>
            <Link to="/app/subjects"
              className="inline-flex items-center gap-2 bg-white/5 hover:bg-white/10 border border-white/10 text-slate-200 px-8 py-4 rounded-2xl font-semibold text-base transition-all">
              Explore Subjects
            </Link>
          </div>
        </motion.div>

        {/* Stats */}
        <motion.div
          initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }}
          className="flex flex-wrap justify-center gap-12 mt-20 pt-10 border-t border-white/5"
        >
          {STATS.map(({ value, label }, i) => (
            <div key={i} className="text-center">
              <div className="text-3xl font-bold text-white mb-1">{value}</div>
              <div className="text-sm text-slate-500">{label}</div>
            </div>
          ))}
        </motion.div>
      </section>

      {/* Dashboard preview */}
      <section className="max-w-5xl mx-auto px-6 pb-24">
        <motion.div initial={{ opacity: 0, y: 30 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ duration: 0.6 }}>
          <div className="rounded-3xl border border-white/8 bg-white/3 overflow-hidden shadow-2xl">
            <div className="bg-[#12121e] border-b border-white/5 px-5 py-3 flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-red-500/60" />
              <div className="w-3 h-3 rounded-full bg-amber-500/60" />
              <div className="w-3 h-3 rounded-full bg-emerald-500/60" />
              <span className="ml-3 text-xs text-slate-600">app.leximind.ai/app</span>
            </div>
            <div className="p-6 grid grid-cols-3 gap-4">
              {/* Sidebar preview */}
              <div className="space-y-1.5">
                {["Dashboard","Learn","Subjects","Learning Path","Quizzes","PYQs","Progress"].map((item, i) => (
                  <div key={i} className={`px-3 py-2 rounded-lg text-xs flex items-center gap-2 ${i === 0 ? "bg-indigo-600/30 text-indigo-300" : "text-slate-500"}`}>
                    <div className={`w-1.5 h-1.5 rounded-full ${i === 0 ? "bg-indigo-400" : "bg-slate-600"}`} />
                    {item}
                  </div>
                ))}
              </div>
              {/* Main content preview */}
              <div className="col-span-2 space-y-3">
                <div className="bg-white/4 rounded-2xl p-4 border border-white/5">
                  <div className="text-xs text-slate-500 mb-2">Continue Learning</div>
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-indigo-600/30 flex items-center justify-center text-indigo-300 text-sm">📐</div>
                    <div>
                      <div className="text-sm font-semibold text-white">Euler's Theorem</div>
                      <div className="text-xs text-slate-500">Engineering Mathematics I · 35 min</div>
                    </div>
                    <div className="ml-auto text-xs bg-amber-500/20 text-amber-300 px-2 py-0.5 rounded-lg">In Progress</div>
                  </div>
                  <div className="mt-3 bg-white/5 rounded-full h-1.5">
                    <div className="bg-indigo-500 h-1.5 rounded-full w-[30%]" />
                  </div>
                </div>
                <div className="grid grid-cols-3 gap-2">
                  {[
                    { label: "Mastered", val: "3", color: "text-emerald-400" },
                    { label: "In Progress", val: "4", color: "text-amber-400" },
                    { label: "Quiz Score", val: "78%", color: "text-indigo-400" },
                  ].map(({ label, val, color }) => (
                    <div key={label} className="bg-white/4 rounded-xl p-3 border border-white/5 text-center">
                      <div className={`text-xl font-bold ${color}`}>{val}</div>
                      <div className="text-[10px] text-slate-500 mt-0.5">{label}</div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </motion.div>
      </section>

      {/* Features */}
      <section className="max-w-6xl mx-auto px-6 pb-24">
        <div className="text-center mb-14">
          <h2 className="text-4xl font-bold text-white mb-4">Built for how students actually study</h2>
          <p className="text-slate-400 text-lg">Every feature is designed around your curriculum, not generic AI tools.</p>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {FEATURES.map(({ icon: Icon, title, desc, color }, i) => (
            <motion.div key={i} initial={{ opacity: 0, y: 16 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: i * 0.08 }}
              className="bg-white/3 border border-white/6 rounded-2xl p-6 hover:bg-white/5 transition-all">
              <div className={`w-11 h-11 rounded-xl bg-gradient-to-br ${color} flex items-center justify-center mb-4 shadow-lg`}>
                <Icon size={20} className="text-white" />
              </div>
              <h3 className="text-white font-semibold text-lg mb-2">{title}</h3>
              <p className="text-slate-400 text-sm leading-relaxed">{desc}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="max-w-3xl mx-auto px-6 pb-24 text-center">
        <div className="bg-gradient-to-br from-indigo-600/20 to-purple-600/20 border border-indigo-500/20 rounded-3xl p-12">
          <h2 className="text-3xl font-bold text-white mb-4">Ready to study smarter?</h2>
          <p className="text-slate-400 mb-8">Set up your profile in 2 minutes. No credit card. Free to start.</p>
          <Link to="/onboarding"
            className="inline-flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500 text-white px-8 py-4 rounded-2xl font-semibold transition-all shadow-xl shadow-indigo-500/25">
            Get Started <ArrowRight size={18} />
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-white/5 py-8 text-center text-slate-600 text-sm">
        LexiMind AI · Adaptive Learning Platform · © 2025
      </footer>
    </div>
  );
}
