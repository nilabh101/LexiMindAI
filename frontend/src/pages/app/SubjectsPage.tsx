import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { Clock, BookOpen, ChevronRight } from "lucide-react";
import { loadUser } from "../../store/userStore";
import { DEMO_USER, DEMO_MASTERY } from "../../data/demoData";
import { getSubjectsByCourse, getChaptersBySubject } from "../../data/curriculum";
import { masteryColor } from "../../services/adaptiveEngine";

const COLOR_MAP: Record<string, string> = {
  indigo: "from-indigo-500 to-purple-500",
  blue: "from-blue-500 to-cyan-500",
  emerald: "from-emerald-500 to-teal-500",
  purple: "from-purple-500 to-pink-500",
  teal: "from-teal-500 to-cyan-500",
  amber: "from-amber-500 to-orange-500",
};

export function SubjectsPage() {
  const user = loadUser() ?? DEMO_USER;
  const courseId = user.academicProfile?.courseId ?? "";
  const subjects = getSubjectsByCourse(courseId);

  return (
    <div className="p-6 lg:p-8 max-w-5xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white">Subjects</h1>
        <p className="text-slate-400 text-sm mt-1">Browse your curriculum and dive into any subject.</p>
      </div>

      {subjects.length === 0 ? (
        <div className="bg-white/3 border border-white/6 rounded-2xl p-14 text-center">
          <BookOpen size={40} className="text-slate-600 mx-auto mb-4" />
          <p className="text-slate-400">No subjects configured for your course yet.</p>
          <p className="text-slate-500 text-sm mt-2">Complete onboarding or check back soon.</p>
          <Link to="/onboarding" className="inline-flex items-center gap-2 mt-4 text-indigo-400 text-sm hover:text-indigo-300">
            Update Profile <ChevronRight size={14} />
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {subjects.map((sub, i) => {
            const chapters = getChaptersBySubject(sub.id);
            const relevantMastery = DEMO_MASTERY.filter(m => {
              // Approximate: check by subjectId on concepts
              return true;
            });
            const avgMastery = 55; // demo value

            return (
              <motion.div key={sub.id} initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.06 }}>
                <Link to={`/app/subjects/${sub.id}`}>
                  <div className="bg-white/3 border border-white/6 rounded-2xl p-6 hover:bg-white/5 hover:border-white/10 transition-all group cursor-pointer">
                    {/* Icon + title */}
                    <div className="flex items-start gap-4 mb-5">
                      <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${COLOR_MAP[sub.color] ?? COLOR_MAP.indigo} flex items-center justify-center text-2xl shrink-0 shadow-lg`}>
                        {sub.icon}
                      </div>
                      <div>
                        <div className="font-semibold text-white text-base leading-snug group-hover:text-indigo-300 transition-colors">{sub.name}</div>
                        {sub.semester && <div className="text-xs text-slate-500 mt-0.5">Semester {sub.semester}</div>}
                      </div>
                    </div>

                    <p className="text-slate-400 text-sm mb-5 line-clamp-2">{sub.description}</p>

                    {/* Stats */}
                    <div className="flex items-center gap-4 text-xs text-slate-500 mb-4">
                      <span className="flex items-center gap-1"><BookOpen size={11} />{sub.totalChapters} chapters</span>
                      <span className="flex items-center gap-1"><Clock size={11} />
                        {chapters.reduce((s, c) => s + c.estimatedMinutes, 0)} min
                      </span>
                    </div>

                    {/* Mastery bar */}
                    <div className="bg-white/5 rounded-full h-1.5 mb-1.5">
                      <div className={`h-1.5 rounded-full bg-gradient-to-r ${COLOR_MAP[sub.color] ?? COLOR_MAP.indigo}`}
                        style={{ width: `${avgMastery}%` }} />
                    </div>
                    <div className="flex items-center justify-between">
                      <span className={`text-xs font-semibold ${masteryColor(avgMastery)}`}>{avgMastery}% mastered</span>
                      <ChevronRight size={14} className="text-slate-600 group-hover:text-indigo-400 transition-colors" />
                    </div>
                  </div>
                </Link>
              </motion.div>
            );
          })}
        </div>
      )}
    </div>
  );
}
