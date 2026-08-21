import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { Brain, ChevronRight, ChevronLeft, Check } from "lucide-react";
import { COURSES, getSubjectsByCourse, getCoursesByLevel } from "../../data/curriculum";
import { completeOnboarding, loadOnboarding, saveOnboarding } from "../../store/userStore";
import type { OnboardingState } from "../../store/userStore";
import type { StudyGoal } from "../../types/education";

const TOTAL_STEPS = 6;

const STUDY_GOALS: { id: StudyGoal; label: string; icon: string }[] = [
  { id: "score_higher",      label: "Score higher in exams",        icon: "🎯" },
  { id: "pass_exams",        label: "Pass my upcoming exams",       icon: "📋" },
  { id: "master_concepts",   label: "Master concepts deeply",       icon: "🧠" },
  { id: "complete_syllabus", label: "Complete my full syllabus",    icon: "📚" },
  { id: "practice_pyqs",     label: "Practice previous year Qs",   icon: "📝" },
  { id: "competitive_exam",  label: "Competitive exam preparation", icon: "🏆" },
];

const STUDY_TIMES = [
  { value: 15,  label: "15 min / day" },
  { value: 30,  label: "30 min / day" },
  { value: 60,  label: "1 hour / day" },
  { value: 120, label: "2 hours / day" },
  { value: 180, label: "3+ hours / day" },
];

function ProgressDots({ current, total }: { current: number; total: number }) {
  return (
    <div className="flex items-center gap-2">
      {Array.from({ length: total }, (_, i) => (
        <div key={i} className={`rounded-full transition-all duration-300 ${i < current ? "w-6 h-2 bg-indigo-500" : i === current ? "w-6 h-2 bg-indigo-500/70" : "w-2 h-2 bg-white/15"}`} />
      ))}
    </div>
  );
}

function OptionCard({ selected, onClick, children }: { selected?: boolean; onClick: () => void; children: React.ReactNode }) {
  return (
    <button onClick={onClick}
      className={`w-full text-left px-5 py-4 rounded-2xl border transition-all duration-200 flex items-center justify-between group
        ${selected ? "border-indigo-500/60 bg-indigo-600/20 text-white" : "border-white/8 bg-white/3 text-slate-300 hover:bg-white/6 hover:border-white/15"}`}>
      {children}
      {selected && <Check size={16} className="text-indigo-400 shrink-0 ml-2" />}
    </button>
  );
}

export function OnboardingPage() {
  const navigate = useNavigate();
  const [state, setState] = useState<OnboardingState>(() => loadOnboarding());

  const update = (patch: Partial<OnboardingState>) => {
    const next = { ...state, ...patch };
    setState(next);
    saveOnboarding(next);
  };

  const next = () => update({ step: state.step + 1 });
  const prev = () => update({ step: Math.max(1, state.step - 1) });

  const finish = () => {
    completeOnboarding(state);
    navigate("/app");
  };

  const schoolClasses = Array.from({ length: 7 }, (_, i) => ({ year: i + 6, label: `Class ${i + 6}` }));
  const collegeYears = Array.from({ length: 4 }, (_, i) => ({ year: i + 1, label: `Year ${i + 1}` }));

  const availableCourses = state.educationLevel
    ? getCoursesByLevel(state.educationLevel).filter(c => {
        if (state.educationLevel === "school") return c.yearRange.includes(state.year ?? 0);
        return true;
      })
    : [];

  const selectedCourse = COURSES.find(c => c.id === state.courseId);
  const availableStreams = selectedCourse?.streams ?? [];

  const availableSubjects = state.courseId ? getSubjectsByCourse(state.courseId) : [];

  const toggleSubject = (id: string) => {
    const ids = state.subjectIds.includes(id)
      ? state.subjectIds.filter(s => s !== id)
      : [...state.subjectIds, id];
    update({ subjectIds: ids });
  };

  const canProceed = () => {
    switch (state.step) {
      case 1: return !!state.educationLevel;
      case 2: return !!state.year;
      case 3: return !!state.courseId;
      case 4: return state.subjectIds.length > 0;
      case 5: return !!state.studyGoal;
      case 6: return !!state.dailyMinutes;
      default: return false;
    }
  };

  return (
    <div className="min-h-screen bg-[#0a0a14] flex flex-col items-center justify-center p-4">
      {/* Logo */}
      <div className="flex items-center gap-2 mb-10">
        <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
          <Brain size={16} className="text-white" />
        </div>
        <span className="font-bold text-white">LexiMind AI</span>
      </div>

      <div className="w-full max-w-lg">
        {/* Progress */}
        <div className="flex items-center justify-between mb-8">
          <ProgressDots current={state.step - 1} total={TOTAL_STEPS} />
          <span className="text-xs text-slate-500">Step {state.step} of {TOTAL_STEPS}</span>
        </div>

        <AnimatePresence mode="wait">
          <motion.div key={state.step} initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} transition={{ duration: 0.2 }}
            className="bg-white/3 border border-white/8 rounded-3xl p-8">

            {/* Step 1: Education level */}
            {state.step === 1 && (
              <div>
                <h2 className="text-2xl font-bold text-white mb-2">What are you studying?</h2>
                <p className="text-slate-400 text-sm mb-6">Choose your education level to get started.</p>
                <div className="space-y-3">
                  <OptionCard selected={state.educationLevel === "school"} onClick={() => update({ educationLevel: "school", year: undefined, courseId: undefined, subjectIds: [] })}>
                    <div className="flex items-center gap-3"><span className="text-2xl">🏫</span><div><div className="font-semibold">School</div><div className="text-xs text-slate-500">Class 6 to Class 12</div></div></div>
                  </OptionCard>
                  <OptionCard selected={state.educationLevel === "college"} onClick={() => update({ educationLevel: "college", year: undefined, courseId: undefined, subjectIds: [] })}>
                    <div className="flex items-center gap-3"><span className="text-2xl">🎓</span><div><div className="font-semibold">College / University</div><div className="text-xs text-slate-500">Year 1 to Year 4</div></div></div>
                  </OptionCard>
                </div>
              </div>
            )}

            {/* Step 2: Year/Class */}
            {state.step === 2 && (
              <div>
                <h2 className="text-2xl font-bold text-white mb-2">{state.educationLevel === "school" ? "Which class are you in?" : "Which year are you in?"}</h2>
                <p className="text-slate-400 text-sm mb-6">This helps us tailor your curriculum.</p>
                <div className="grid grid-cols-2 gap-2">
                  {(state.educationLevel === "school" ? schoolClasses : collegeYears).map(({ year, label }) => (
                    <OptionCard key={year} selected={state.year === year} onClick={() => update({ year, courseId: undefined, subjectIds: [] })}>
                      <span className="font-semibold">{label}</span>
                    </OptionCard>
                  ))}
                </div>
              </div>
            )}

            {/* Step 3: Course/Stream */}
            {state.step === 3 && (
              <div>
                <h2 className="text-2xl font-bold text-white mb-2">{state.educationLevel === "school" ? "Choose your stream" : "Choose your course"}</h2>
                <p className="text-slate-400 text-sm mb-6">
                  {state.educationLevel === "school" ? "Select your subject stream." : "What degree are you pursuing?"}
                </p>
                <div className="space-y-2 max-h-72 overflow-y-auto">
                  {availableCourses.length === 0 ? (
                    <div className="text-slate-400 text-sm text-center py-4">More courses coming soon!</div>
                  ) : availableCourses.map(course => (
                    <OptionCard key={course.id} selected={state.courseId === course.id} onClick={() => update({ courseId: course.id, subjectIds: [] })}>
                      <span className="font-medium">{course.name}</span>
                    </OptionCard>
                  ))}
                  {/* If college and no streams, also show stream-agnostic for school */}
                  {state.educationLevel === "school" && state.year && state.year <= 10 && availableCourses.length === 0 && (
                    <OptionCard selected={state.courseId === `class-${state.year}`} onClick={() => update({ courseId: `class-${state.year}`, subjectIds: [] })}>
                      <span className="font-medium">Class {state.year}</span>
                    </OptionCard>
                  )}
                </div>
              </div>
            )}

            {/* Step 4: Subjects */}
            {state.step === 4 && (
              <div>
                <h2 className="text-2xl font-bold text-white mb-2">Choose your subjects</h2>
                <p className="text-slate-400 text-sm mb-6">Select the subjects you want to study. You can add more later.</p>
                {availableSubjects.length === 0 ? (
                  <div className="text-slate-400 text-sm text-center py-8">
                    No subjects available for this course yet.<br />
                    <span className="text-xs">More content coming soon. You can continue and add subjects later.</span>
                  </div>
                ) : (
                  <div className="space-y-2 max-h-64 overflow-y-auto">
                    {availableSubjects.map(sub => (
                      <OptionCard key={sub.id} selected={state.subjectIds.includes(sub.id)} onClick={() => toggleSubject(sub.id)}>
                        <div className="flex items-center gap-3">
                          <span className="text-xl">{sub.icon}</span>
                          <div>
                            <div className="font-medium">{sub.name}</div>
                            <div className="text-xs text-slate-500">{sub.totalChapters} chapters</div>
                          </div>
                        </div>
                      </OptionCard>
                    ))}
                  </div>
                )}
                {state.subjectIds.length === 0 && availableSubjects.length === 0 && (
                  <p className="text-xs text-slate-500 text-center mt-2">Click Next to continue without selecting subjects.</p>
                )}
              </div>
            )}

            {/* Step 5: Study goal */}
            {state.step === 5 && (
              <div>
                <h2 className="text-2xl font-bold text-white mb-2">What's your learning goal?</h2>
                <p className="text-slate-400 text-sm mb-6">We'll personalise your learning path around this.</p>
                <div className="space-y-2">
                  {STUDY_GOALS.map(g => (
                    <OptionCard key={g.id} selected={state.studyGoal === g.id} onClick={() => update({ studyGoal: g.id })}>
                      <div className="flex items-center gap-3"><span className="text-xl">{g.icon}</span><span className="font-medium">{g.label}</span></div>
                    </OptionCard>
                  ))}
                </div>
              </div>
            )}

            {/* Step 6: Study time */}
            {state.step === 6 && (
              <div>
                <h2 className="text-2xl font-bold text-white mb-2">How much time can you study daily?</h2>
                <p className="text-slate-400 text-sm mb-6">We'll fit your learning plan within this time.</p>
                <div className="grid grid-cols-2 gap-2">
                  {STUDY_TIMES.map(t => (
                    <OptionCard key={t.value} selected={state.dailyMinutes === t.value} onClick={() => update({ dailyMinutes: t.value })}>
                      <span className="font-semibold">{t.label}</span>
                    </OptionCard>
                  ))}
                </div>
              </div>
            )}

          </motion.div>
        </AnimatePresence>

        {/* Navigation */}
        <div className="flex items-center justify-between mt-6">
          <button onClick={prev} disabled={state.step === 1}
            className="flex items-center gap-1.5 text-sm text-slate-400 hover:text-white disabled:opacity-30 transition-all">
            <ChevronLeft size={16} /> Back
          </button>
          {state.step < TOTAL_STEPS ? (
            <button onClick={next} disabled={!canProceed() && !(state.step === 4 && availableSubjects.length === 0)}
              className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 disabled:cursor-not-allowed text-white px-6 py-2.5 rounded-xl font-semibold text-sm transition-all">
              Continue <ChevronRight size={15} />
            </button>
          ) : (
            <button onClick={finish} disabled={!canProceed()}
              className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 disabled:cursor-not-allowed text-white px-6 py-2.5 rounded-xl font-semibold text-sm transition-all">
              Start Learning <ChevronRight size={15} />
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
