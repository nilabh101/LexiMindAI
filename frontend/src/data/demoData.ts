/**
 * DEMO DATA — isolated from real application data.
 * Used ONLY for visual/UI development.
 * Never presented as real AI predictions or real student data.
 * Will be replaced by real API data in Phase 2.
 */

import type {
  User, Mastery, LearningPathItem, QuizAttempt, ProgressStats, StudySession
} from "../types/education";

export const DEMO_USER: User = {
  id: "demo-user-1",
  name: "Arjun Sharma",
  email: "arjun@example.com",
  createdAt: "2025-01-10T00:00:00Z",
  onboardingComplete: true,
  studyGoal: "master_concepts",
  dailyStudyMinutes: 60,
  streak: 7,
  academicProfile: {
    educationLevel: "college",
    year: 1,
    courseId: "btech-cse",
    semesterId: "sem-1",
    subjectIds: ["em1-btech", "programming-btech", "physics-btech"],
  },
};

export const DEMO_MASTERY: Mastery[] = [
  { userId: "demo-user-1", conceptId: "limits-dc",             score: 85, status: "mastered",     lastAttempted: "2025-01-14", attemptCount: 4 },
  { userId: "demo-user-1", conceptId: "derivatives-dc",        score: 78, status: "mastered",     lastAttempted: "2025-01-15", attemptCount: 3 },
  { userId: "demo-user-1", conceptId: "partial-derivatives-dc",score: 62, status: "in_progress",  lastAttempted: "2025-01-16", attemptCount: 2 },
  { userId: "demo-user-1", conceptId: "euler-theorem-dc",      score: 30, status: "in_progress",  lastAttempted: "2025-01-16", attemptCount: 1 },
  { userId: "demo-user-1", conceptId: "total-derivatives-dc",  score: 0,  status: "not_started",  attemptCount: 0 },
  { userId: "demo-user-1", conceptId: "c-basics",              score: 92, status: "mastered",     lastAttempted: "2025-01-12", attemptCount: 5 },
  { userId: "demo-user-1", conceptId: "loops-c",               score: 70, status: "in_progress",  lastAttempted: "2025-01-15", attemptCount: 2 },
  { userId: "demo-user-1", conceptId: "discriminant",          score: 45, status: "needs_review", lastAttempted: "2025-01-10", attemptCount: 2 },
  { userId: "demo-user-1", conceptId: "trig-ratios",           score: 0,  status: "not_started",  attemptCount: 0 },
];

export const DEMO_LEARNING_PATH: LearningPathItem[] = [
  { id: "lp-1", conceptId: "limits-dc",             order: 1, status: "mastered",     mastery: 85, estimatedMinutes: 30, isCurrentFocus: false },
  { id: "lp-2", conceptId: "derivatives-dc",        order: 2, status: "mastered",     mastery: 78, estimatedMinutes: 35, isCurrentFocus: false },
  { id: "lp-3", conceptId: "partial-derivatives-dc",order: 3, status: "in_progress",  mastery: 62, estimatedMinutes: 40, isCurrentFocus: false },
  { id: "lp-4", conceptId: "euler-theorem-dc",      order: 4, status: "in_progress",  mastery: 30, estimatedMinutes: 35, isCurrentFocus: true  },
  { id: "lp-5", conceptId: "total-derivatives-dc",  order: 5, status: "available",    mastery: 0,  estimatedMinutes: 40, isCurrentFocus: false },
  { id: "lp-6", conceptId: "matrix-ops",            order: 6, status: "locked",       mastery: 0,  estimatedMinutes: 45, isCurrentFocus: false },
  { id: "lp-7", conceptId: "determinants",          order: 7, status: "locked",       mastery: 0,  estimatedMinutes: 40, isCurrentFocus: false },
];

export const DEMO_PROGRESS: ProgressStats = {
  totalConcepts: 9,
  masteredConcepts: 3,
  inProgressConcepts: 4,
  needsReviewConcepts: 1,
  totalQuizAttempts: 12,
  pyqsSolved: 8,
  totalStudyMinutes: 340,
  streak: 7,
  subjectMastery: [
    { subjectId: "em1-btech",          mastery: 55 },
    { subjectId: "programming-btech",  mastery: 81 },
    { subjectId: "physics-btech",      mastery: 20 },
  ],
};

export const DEMO_RECENT_SESSIONS: StudySession[] = [
  { id: "s1", userId: "demo-user-1", conceptId: "euler-theorem-dc",      subjectId: "em1-btech",         type: "study", durationMinutes: 35, date: "2025-01-16" },
  { id: "s2", userId: "demo-user-1", subjectId: "programming-btech",                                     type: "quiz",  durationMinutes: 15, date: "2025-01-15" },
  { id: "s3", userId: "demo-user-1", conceptId: "partial-derivatives-dc", subjectId: "em1-btech",        type: "pyq",   durationMinutes: 20, date: "2025-01-15" },
  { id: "s4", userId: "demo-user-1", conceptId: "derivatives-dc",         subjectId: "em1-btech",        type: "study", durationMinutes: 40, date: "2025-01-14" },
];

// Demo PYQs
export const DEMO_PYQS = [
  {
    id: "pyq-1",
    question: "If u = x² + y² + z², find the value of x·(∂u/∂x) + y·(∂u/∂y) + z·(∂u/∂z).",
    year: 2023, marks: 5, difficulty: "medium",
    conceptId: "euler-theorem-dc", subjectId: "em1-btech",
    solution: "u is homogeneous of degree 2. By Euler's theorem, the answer is 2u = 2(x²+y²+z²).",
    explanation: "Apply Euler's theorem: since u = x²+y²+z² is homogeneous of degree n=2, the sum equals n·u = 2u.",
    source: "RGPV 2023",
  },
  {
    id: "pyq-2",
    question: "Verify Euler's theorem for f(x,y) = x³ + y³ + 3x²y.",
    year: 2022, marks: 7, difficulty: "medium",
    conceptId: "euler-theorem-dc", subjectId: "em1-btech",
    solution: "f is homogeneous of degree 3. Compute ∂f/∂x = 3x²+6xy and ∂f/∂y = 3y²+3x². Then x·(∂f/∂x) + y·(∂f/∂y) = 3x³+6x²y+3y³+3x²y = 3(x³+y³+3x²y) = 3f. ✓",
    explanation: "Homogeneous of degree 3, so n·f = 3f.",
    source: "RGPV 2022",
  },
  {
    id: "pyq-3",
    question: "Write a C program to print the Fibonacci series up to n terms.",
    year: 2023, marks: 5, difficulty: "easy",
    conceptId: "loops-c", subjectId: "programming-btech",
    solution: "Use a for loop with two variables tracking previous two terms.",
    explanation: "Initialize a=0, b=1. In each iteration print a, then update: temp=a+b, a=b, b=temp.",
    source: "RGPV 2023",
  },
];

// Demo LexiMind notes
export const DEMO_NOTES = [
  {
    id: "note-euler",
    title: "Euler's Theorem — Complete Notes",
    subjectId: "em1-btech", chapterId: "dc-em1", conceptId: "euler-theorem-dc",
    type: "leximind" as const,
    content: `# Euler's Theorem on Homogeneous Functions\n\n## Definition\nA function f(x, y) is called **homogeneous of degree n** if:\nf(tx, ty) = tⁿ · f(x, y) for all t.\n\n## Theorem Statement\nIf f(x, y) is a homogeneous function of degree n and has continuous partial derivatives, then:\n\n**x · (∂f/∂x) + y · (∂f/∂y) = n · f**\n\n## Corollary\nFor second-order partial derivatives:\nx² · (∂²f/∂x²) + 2xy · (∂²f/∂x∂y) + y² · (∂²f/∂y²) = n(n-1) · f\n\n## Example\nLet f(x,y) = x³ + y³ + 3x²y (degree 3)\n- ∂f/∂x = 3x² + 6xy\n- ∂f/∂y = 3y² + 3x²\n- x(3x²+6xy) + y(3y²+3x²) = 3x³+6x²y+3y³+3x²y = 3f ✓\n`,
    summary: "Euler's theorem states that for a homogeneous function of degree n, x·∂f/∂x + y·∂f/∂y = n·f.",
    keyPoints: ["Homogeneous function definition", "Euler's theorem formula", "Corollary for second derivatives"],
    formulas: ["x·(∂f/∂x) + y·(∂f/∂y) = n·f"],
    createdAt: "2025-01-01T00:00:00Z", updatedAt: "2025-01-15T00:00:00Z",
  },
  {
    id: "note-partial",
    title: "Partial Derivatives — Notes",
    subjectId: "em1-btech", chapterId: "dc-em1", conceptId: "partial-derivatives-dc",
    type: "leximind" as const,
    content: `# Partial Derivatives\n\n## Introduction\nFor a function f(x, y) of two variables, the **partial derivative** with respect to x is the rate of change holding y constant.\n\n## Notation\n- ∂f/∂x or fₓ — partial with respect to x\n- ∂f/∂y or f_y — partial with respect to y\n\n## Higher Order\n- ∂²f/∂x² — second partial w.r.t. x\n- ∂²f/∂x∂y — mixed partial derivative\n\n## Clairaut's Theorem\nFor continuous mixed partials: ∂²f/∂x∂y = ∂²f/∂y∂x\n`,
    summary: "Partial derivatives treat one variable as constant while differentiating with respect to another.",
    keyPoints: ["∂f/∂x holds y constant", "Mixed partials are equal (Clairaut's)", "Higher order notation"],
    formulas: ["∂f/∂x = lim(h→0)[f(x+h,y)-f(x,y)]/h"],
    createdAt: "2025-01-01T00:00:00Z", updatedAt: "2025-01-14T00:00:00Z",
  },
];
