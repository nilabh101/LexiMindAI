/**
 * Curriculum configuration data.
 * This is the master data model for courses, subjects, chapters, concepts.
 * In production this will come from the API. For Phase 1 we use this as demo data.
 * All demo data is clearly isolated here — never mixed with real student data.
 */

import type { Course, Subject, Chapter, Concept } from "../types/education";

// ─── Courses ──────────────────────────────────────────────────────────────────

export const COURSES: Course[] = [
  // School
  { id: "class-6",  name: "Class 6",  educationLevel: "school", yearRange: [6] },
  { id: "class-7",  name: "Class 7",  educationLevel: "school", yearRange: [7] },
  { id: "class-8",  name: "Class 8",  educationLevel: "school", yearRange: [8] },
  { id: "class-9",  name: "Class 9",  educationLevel: "school", yearRange: [9] },
  { id: "class-10", name: "Class 10", educationLevel: "school", yearRange: [10] },
  {
    id: "class-11", name: "Class 11", educationLevel: "school", yearRange: [11],
    streams: [
      { id: "science",  name: "Science",  subjects: ["physics-11", "chemistry-11", "maths-11", "biology-11"] },
      { id: "commerce", name: "Commerce", subjects: ["accounts-11", "economics-11", "business-11", "maths-11"] },
      { id: "arts",     name: "Arts",     subjects: ["history-11", "geography-11", "political-science-11", "economics-11"] },
    ],
  },
  {
    id: "class-12", name: "Class 12", educationLevel: "school", yearRange: [12],
    streams: [
      { id: "science",  name: "Science",  subjects: ["physics-12", "chemistry-12", "maths-12", "biology-12"] },
      { id: "commerce", name: "Commerce", subjects: ["accounts-12", "economics-12", "business-12", "maths-12"] },
      { id: "arts",     name: "Arts",     subjects: ["history-12", "geography-12", "political-science-12", "economics-12"] },
    ],
  },
  // College
  { id: "btech-cse",  name: "B.Tech CSE",        shortName: "CSE",   educationLevel: "college", yearRange: [1,2,3,4] },
  { id: "btech-ece",  name: "B.Tech ECE",        shortName: "ECE",   educationLevel: "college", yearRange: [1,2,3,4] },
  { id: "btech-mech", name: "B.Tech Mechanical",  shortName: "Mech",  educationLevel: "college", yearRange: [1,2,3,4] },
  { id: "btech-civil",name: "B.Tech Civil",       shortName: "Civil", educationLevel: "college", yearRange: [1,2,3,4] },
  { id: "bca",        name: "BCA",               shortName: "BCA",   educationLevel: "college", yearRange: [1,2,3] },
  { id: "bsc-cs",     name: "B.Sc Computer Science", shortName: "B.Sc CS", educationLevel: "college", yearRange: [1,2,3] },
  { id: "bsc-maths",  name: "B.Sc Mathematics",  shortName: "B.Sc Maths", educationLevel: "college", yearRange: [1,2,3] },
  { id: "bcom",       name: "B.Com",             shortName: "B.Com", educationLevel: "college", yearRange: [1,2,3] },
  { id: "bba",        name: "BBA",               shortName: "BBA",   educationLevel: "college", yearRange: [1,2,3] },
  { id: "ba",         name: "B.A",               shortName: "B.A",   educationLevel: "college", yearRange: [1,2,3] },
];

// ─── Subjects (starter set — expandable via API) ──────────────────────────────

export const SUBJECTS: Subject[] = [
  // B.Tech CSE — Semester 1
  {
    id: "em1-btech",
    name: "Engineering Mathematics I",
    shortName: "EM-I",
    courseId: "btech-cse",
    semester: 1, year: 1,
    color: "indigo",
    icon: "📐",
    description: "Differential calculus, matrices, and complex numbers.",
    chapterIds: ["dc-em1", "matrices-em1", "complex-em1"],
    totalChapters: 3,
  },
  {
    id: "programming-btech",
    name: "Programming in C",
    shortName: "C Prog",
    courseId: "btech-cse",
    semester: 1, year: 1,
    color: "blue",
    icon: "💻",
    description: "Introduction to programming using C language.",
    chapterIds: ["intro-c", "control-flow-c", "functions-c", "arrays-c", "pointers-c"],
    totalChapters: 5,
  },
  {
    id: "physics-btech",
    name: "Engineering Physics",
    shortName: "Phy",
    courseId: "btech-cse",
    semester: 1, year: 1,
    color: "emerald",
    icon: "⚛️",
    description: "Optics, wave mechanics, and quantum physics.",
    chapterIds: ["optics-phy", "waves-phy", "quantum-phy"],
    totalChapters: 3,
  },
  // Class 10
  {
    id: "maths-10",
    name: "Mathematics",
    shortName: "Maths",
    courseId: "class-10",
    year: 10,
    color: "purple",
    icon: "➗",
    description: "Algebra, geometry, trigonometry, and statistics.",
    chapterIds: ["real-numbers-10", "polynomials-10", "quadratic-10", "trig-10", "circles-10", "stats-10"],
    totalChapters: 6,
  },
  {
    id: "science-10",
    name: "Science",
    shortName: "Sci",
    courseId: "class-10",
    year: 10,
    color: "teal",
    icon: "🔬",
    description: "Physics, Chemistry, and Biology.",
    chapterIds: ["chemical-reactions-10", "electricity-10", "heredity-10", "light-10"],
    totalChapters: 4,
  },
];

// ─── Chapters ─────────────────────────────────────────────────────────────────

export const CHAPTERS: Chapter[] = [
  // EM-I
  {
    id: "dc-em1",
    name: "Differential Calculus",
    subjectId: "em1-btech",
    order: 1,
    estimatedMinutes: 180,
    conceptIds: ["limits-dc", "derivatives-dc", "partial-derivatives-dc", "euler-theorem-dc", "total-derivatives-dc"],
    description: "Limits, derivatives, partial derivatives, and their applications.",
  },
  {
    id: "matrices-em1",
    name: "Matrices & Linear Algebra",
    subjectId: "em1-btech",
    order: 2,
    estimatedMinutes: 150,
    conceptIds: ["matrix-ops", "determinants", "eigen-values", "cayley-hamilton"],
    description: "Matrix operations, determinants, eigenvalues, and eigenvectors.",
  },
  // Programming in C
  {
    id: "intro-c",
    name: "Introduction to C",
    subjectId: "programming-btech",
    order: 1,
    estimatedMinutes: 90,
    conceptIds: ["c-basics", "data-types-c", "operators-c"],
    description: "History, structure, compilation, variables, and data types.",
  },
  {
    id: "control-flow-c",
    name: "Control Flow",
    subjectId: "programming-btech",
    order: 2,
    estimatedMinutes: 120,
    conceptIds: ["if-else-c", "loops-c", "switch-c"],
    description: "Decision making, loops, and branching statements.",
  },
  // Class 10 Maths
  {
    id: "real-numbers-10",
    name: "Real Numbers",
    subjectId: "maths-10",
    order: 1,
    estimatedMinutes: 60,
    conceptIds: ["euclid-division", "fundamental-theorem", "irrational-numbers"],
    description: "Euclid's division lemma, fundamental theorem of arithmetic.",
  },
  {
    id: "quadratic-10",
    name: "Quadratic Equations",
    subjectId: "maths-10",
    order: 3,
    estimatedMinutes: 90,
    conceptIds: ["quad-roots", "discriminant", "nature-of-roots", "sum-product-roots"],
    description: "Methods of solving quadratic equations and their applications.",
  },
  {
    id: "trig-10",
    name: "Trigonometry",
    subjectId: "maths-10",
    order: 4,
    estimatedMinutes: 120,
    conceptIds: ["trig-ratios", "trig-identities", "trig-heights-distances"],
    description: "Trigonometric ratios, identities, and applications.",
  },
];

// ─── Concepts ─────────────────────────────────────────────────────────────────

export const CONCEPTS: Concept[] = [
  // Differential Calculus
  {
    id: "limits-dc",
    name: "Limits and Continuity",
    chapterId: "dc-em1",
    subjectId: "em1-btech",
    difficulty: "beginner",
    estimatedMinutes: 30,
    prerequisites: [],
    description: "Understanding limits, indeterminate forms, L'Hôpital's rule, and continuity.",
    keyPoints: [
      "Limit of a function as x → a",
      "Left-hand and right-hand limits",
      "L'Hôpital's rule for 0/0 and ∞/∞ forms",
      "Continuity at a point and over an interval",
    ],
  },
  {
    id: "derivatives-dc",
    name: "Derivatives",
    chapterId: "dc-em1",
    subjectId: "em1-btech",
    difficulty: "beginner",
    estimatedMinutes: 35,
    prerequisites: ["limits-dc"],
    description: "First principles, standard derivatives, chain rule, product rule, quotient rule.",
    keyPoints: [
      "Definition from first principles",
      "Standard derivatives table",
      "Chain rule for composite functions",
      "Product and quotient rules",
    ],
  },
  {
    id: "partial-derivatives-dc",
    name: "Partial Derivatives",
    chapterId: "dc-em1",
    subjectId: "em1-btech",
    difficulty: "intermediate",
    estimatedMinutes: 40,
    prerequisites: ["derivatives-dc"],
    description: "Partial differentiation of functions with multiple variables.",
    keyPoints: [
      "Partial derivative with respect to x and y",
      "Higher-order partial derivatives",
      "Mixed partial derivatives",
      "Clairaut's theorem",
    ],
    formulaSummary: "∂f/∂x = lim(h→0) [f(x+h,y) - f(x,y)] / h",
  },
  {
    id: "euler-theorem-dc",
    name: "Euler's Theorem",
    chapterId: "dc-em1",
    subjectId: "em1-btech",
    difficulty: "intermediate",
    estimatedMinutes: 35,
    prerequisites: ["partial-derivatives-dc"],
    description: "Euler's theorem on homogeneous functions and its corollary.",
    keyPoints: [
      "Definition of homogeneous function",
      "Euler's theorem: x·∂f/∂x + y·∂f/∂y = n·f",
      "Deductions and corollary",
      "Applications to verify homogeneity",
    ],
    formulaSummary: "If f(x,y) is homogeneous of degree n: x·(∂f/∂x) + y·(∂f/∂y) = n·f",
  },
  {
    id: "total-derivatives-dc",
    name: "Total Derivatives",
    chapterId: "dc-em1",
    subjectId: "em1-btech",
    difficulty: "intermediate",
    estimatedMinutes: 40,
    prerequisites: ["euler-theorem-dc"],
    description: "Total differential, chain rule for partial derivatives.",
    keyPoints: [
      "Total differential df",
      "Chain rule for composite functions",
      "Implicit differentiation",
      "Applications to error analysis",
    ],
    formulaSummary: "df = (∂f/∂x)dx + (∂f/∂y)dy",
  },
  // C Programming
  {
    id: "c-basics",
    name: "C Basics",
    chapterId: "intro-c",
    subjectId: "programming-btech",
    difficulty: "beginner",
    estimatedMinutes: 25,
    prerequisites: [],
    description: "Structure of a C program, compilation, and basic I/O.",
    keyPoints: ["#include, main(), printf, scanf", "Compilation steps", "Variables and identifiers"],
  },
  {
    id: "loops-c",
    name: "Loops in C",
    chapterId: "control-flow-c",
    subjectId: "programming-btech",
    difficulty: "beginner",
    estimatedMinutes: 30,
    prerequisites: ["c-basics"],
    description: "for, while, do-while loops and loop control statements.",
    keyPoints: ["for loop syntax", "while and do-while", "break and continue", "Nested loops"],
  },
  // Class 10
  {
    id: "discriminant",
    name: "Discriminant",
    chapterId: "quadratic-10",
    subjectId: "maths-10",
    difficulty: "intermediate",
    estimatedMinutes: 20,
    prerequisites: ["quad-roots"],
    description: "Using the discriminant to determine the nature of roots.",
    keyPoints: ["D = b² - 4ac", "D > 0: two real distinct roots", "D = 0: two equal roots", "D < 0: no real roots"],
    formulaSummary: "D = b² - 4ac",
  },
  {
    id: "trig-ratios",
    name: "Trigonometric Ratios",
    chapterId: "trig-10",
    subjectId: "maths-10",
    difficulty: "beginner",
    estimatedMinutes: 25,
    prerequisites: [],
    description: "sin, cos, tan, cosec, sec, cot and their values for standard angles.",
    keyPoints: ["SOH-CAH-TOA", "Standard angle values (0°, 30°, 45°, 60°, 90°)", "Reciprocal ratios"],
  },
];

// ─── Lookup helpers ───────────────────────────────────────────────────────────

export function getCoursesByLevel(level: "school" | "college"): Course[] {
  return COURSES.filter(c => c.educationLevel === level);
}

export function getSubjectsByCourse(courseId: string): Subject[] {
  return SUBJECTS.filter(s => s.courseId === courseId);
}

export function getChaptersBySubject(subjectId: string): Chapter[] {
  return CHAPTERS.filter(c => c.subjectId === subjectId).sort((a, b) => a.order - b.order);
}

export function getConceptsByChapter(chapterId: string): Concept[] {
  return CONCEPTS.filter(c => c.chapterId === chapterId);
}

export function getConcept(conceptId: string): Concept | undefined {
  return CONCEPTS.find(c => c.id === conceptId);
}

export function getSubject(subjectId: string): Subject | undefined {
  return SUBJECTS.find(s => s.id === subjectId);
}

export function getChapter(chapterId: string): Chapter | undefined {
  return CHAPTERS.find(c => c.id === chapterId);
}

export function getCourse(courseId: string): Course | undefined {
  return COURSES.find(c => c.id === courseId);
}
