// ─── Core education hierarchy types ──────────────────────────────────────────

export type EducationLevel = "school" | "college";

export interface AcademicProfile {
  educationLevel: EducationLevel;
  year: number;           // class 6-12 for school, year 1-4 for college
  courseId: string;       // e.g. "btech-cse", "bsc", "class-10"
  streamId?: string;      // science/commerce/arts for school
  semesterId?: string;    // current semester
  subjectIds: string[];
}

export interface Course {
  id: string;
  name: string;
  shortName?: string;
  educationLevel: EducationLevel;
  yearRange: number[];    // [1] or [1,2,3,4]
  streams?: Stream[];
  description?: string;
}

export interface Stream {
  id: string;
  name: string;
  subjects: string[];     // subject IDs
}

export interface Subject {
  id: string;
  name: string;
  shortName?: string;
  courseId: string;
  semester?: number;
  year?: number;
  color: string;          // tailwind color class
  icon: string;           // emoji or icon name
  description: string;
  chapterIds: string[];
  totalChapters: number;
}

export interface Chapter {
  id: string;
  name: string;
  subjectId: string;
  order: number;
  estimatedMinutes: number;
  conceptIds: string[];
  description?: string;
}

export interface Concept {
  id: string;
  name: string;
  chapterId: string;
  subjectId: string;
  difficulty: "beginner" | "intermediate" | "advanced";
  estimatedMinutes: number;
  prerequisites: string[];   // concept IDs
  description: string;
  formulaSummary?: string;
  keyPoints: string[];
}

export interface Prerequisite {
  conceptId: string;
  prerequisiteConceptId: string;
  strength: "required" | "recommended";
}

// ─── Questions & Quiz ─────────────────────────────────────────────────────────

export type QuestionType = "mcq" | "fill_blank" | "true_false" | "short_answer";
export type QuestionSource = "PYQ" | "practice" | "generated" | "textbook";

export interface Question {
  id: string;
  conceptId: string;
  subjectId: string;
  chapterId?: string;
  type: QuestionType;
  question: string;
  options?: string[];       // for MCQ
  answer: string;
  acceptedAnswers?: string[]; // for fill_blank
  explanation: string;
  difficulty: "easy" | "medium" | "hard";
  source: QuestionSource;
  year?: number;            // for PYQ
  marks?: number;
  tags?: string[];
}

export interface Quiz {
  id: string;
  title: string;
  subjectId: string;
  chapterId?: string;
  conceptIds: string[];
  questionIds: string[];
  difficulty: "easy" | "medium" | "hard" | "mixed";
  estimatedMinutes: number;
  type: "concept" | "chapter" | "subject" | "pyq" | "weak_areas" | "adaptive";
}

export interface QuizAttempt {
  id: string;
  quizId: string;
  userId: string;
  startedAt: string;
  completedAt?: string;
  answers: Answer[];
  score: number;
  totalQuestions: number;
  correctAnswers: number;
  conceptPerformance: ConceptPerformance[];
}

export interface Answer {
  questionId: string;
  userAnswer: string;
  isCorrect: boolean;
  timeTakenSeconds?: number;
}

export interface ConceptPerformance {
  conceptId: string;
  correct: number;
  total: number;
  masteryDelta: number;
}

// ─── Mastery & Learning Path ──────────────────────────────────────────────────

export type MasteryStatus = "not_started" | "in_progress" | "mastered" | "needs_review";

export interface Mastery {
  userId: string;
  conceptId: string;
  score: number;         // 0-100
  status: MasteryStatus;
  lastAttempted?: string;
  attemptCount: number;
}

export type LearningPathItemStatus = "locked" | "available" | "in_progress" | "mastered" | "needs_review";

export interface LearningPathItem {
  id: string;
  conceptId: string;
  order: number;
  status: LearningPathItemStatus;
  mastery: number;       // 0-100
  estimatedMinutes: number;
  isCurrentFocus: boolean;
}

export interface LearningPath {
  id: string;
  userId: string;
  subjectId: string;
  items: LearningPathItem[];
  generatedAt: string;
  lastUpdated: string;
}

// ─── Notes & Library ─────────────────────────────────────────────────────────

export interface Note {
  id: string;
  title: string;
  subjectId: string;
  chapterId?: string;
  conceptId?: string;
  type: "leximind" | "user";
  content: string;
  summary?: string;
  keyPoints?: string[];
  formulas?: string[];
  createdAt: string;
  updatedAt: string;
}

export type DocumentStatus = "uploaded" | "processing" | "ready" | "failed" | "needs_review";
export type AcademicDocumentType = "STUDY_NOTES" | "PYQ" | "QUESTION_BANK" | "REFERENCE" | "UNKNOWN";

export interface LibraryDocument {
  id: string;
  name: string;
  fileType: "pdf" | "pptx" | "docx" | "txt";
  fileSize: number;
  uploadedAt: string;
  subjectId?: string;
  subject?: string;
  courseId?: string;
  documentType?: AcademicDocumentType | string;
  status: DocumentStatus;
  errorMessage?: string | null;
  ocrRequired?: boolean;
  extractedNoteId?: string;
}

// ─── User & Progress ─────────────────────────────────────────────────────────

export interface User {
  id: string;
  name: string;
  email: string;
  avatarUrl?: string;
  createdAt: string;
  academicProfile?: AcademicProfile;
  onboardingComplete: boolean;
  studyGoal: StudyGoal;
  dailyStudyMinutes: number;
  streak: number;
}

export type StudyGoal =
  | "score_higher"
  | "pass_exams"
  | "master_concepts"
  | "complete_syllabus"
  | "practice_pyqs"
  | "competitive_exam";

export interface StudySession {
  id: string;
  userId: string;
  conceptId?: string;
  subjectId?: string;
  type: "study" | "quiz" | "pyq" | "notes";
  durationMinutes: number;
  date: string;
}

export interface ProgressStats {
  totalConcepts: number;
  masteredConcepts: number;
  inProgressConcepts: number;
  needsReviewConcepts: number;
  totalQuizAttempts: number;
  pyqsSolved: number;
  totalStudyMinutes: number;
  streak: number;
  subjectMastery: { subjectId: string; mastery: number }[];
}
