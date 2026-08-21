/**
 * Adaptive Engine Service — Phase 3.
 * All functions now call the real backend API.
 * Demo data stubs removed.
 */
import { api } from "../lib/api";
import type { Mastery, LearningPathItem, MasteryStatus } from "../types/education";

const DEFAULT_USER_ID = "demo-user-1";

function getUserId(): string {
  try {
    const stored = localStorage.getItem("leximind_user");
    if (stored) {
      const u = JSON.parse(stored);
      return u?.id || DEFAULT_USER_ID;
    }
  } catch {}
  return DEFAULT_USER_ID;
}

// ── Live API calls ─────────────────────────────────────────────────────────────

export async function fetchAllMastery(userId?: string): Promise<Mastery[]> {
  const uid = userId || getUserId();
  const r = await api.get(`/learning/mastery/${uid}`);
  return (r.data || []).map((m: any) => ({
    conceptId: m.conceptId,
    score: m.score ?? m.mastery_score ?? 0,
    status: _mapState(m.state || m.status) as MasteryStatus,
    attemptCount: m.attemptCount ?? m.questionsAttempted ?? 0,
    lastAttempted: m.lastAttempted,
  }));
}

export async function fetchWeakConcepts(userId?: string) {
  const uid = userId || getUserId();
  const r = await api.get(`/learning/weak-concepts/${uid}`);
  return r.data?.weakConcepts || [];
}

export async function fetchRecommendation(userId?: string) {
  const uid = userId || getUserId();
  const r = await api.get(`/learning/recommended/${uid}`);
  return r.data?.recommendation || null;
}

export async function fetchProgress(userId?: string) {
  const uid = userId || getUserId();
  const r = await api.get(`/learning/progress/${uid}`);
  return r.data || {};
}

export async function fetchDailyPlan(userId?: string, studyGoalMinutes = 30) {
  const uid = userId || getUserId();
  const r = await api.get(`/learning/daily-plan/${uid}`, {
    params: { study_goal_minutes: studyGoalMinutes },
  });
  return r.data?.activities || [];
}

export async function fetchReviewSchedule(userId?: string) {
  const uid = userId || getUserId();
  const r = await api.get(`/learning/review-schedule`, { params: { user_id: uid } });
  return r.data?.overdueReviews || [];
}

export async function fetchMistakes(userId?: string, conceptId?: string) {
  const uid = userId || getUserId();
  const params: any = { user_id: uid };
  if (conceptId) params.concept_id = conceptId;
  const r = await api.get(`/learning/mistakes`, { params });
  return r.data?.mistakes || [];
}

export async function updateMasteryAfterQuiz(
  userId: string,
  quizId: string,
  answers: Array<{
    questionId?: number | string;
    conceptId?: string;
    correct: boolean;
    difficulty?: string;
    timeTaken?: number;
  }>
) {
  const r = await api.post(`/learning/quiz-attempt`, {
    userId,
    quizId,
    answers,
  });
  return r.data;
}

// ── Sync helpers (kept for backwards compatibility in components) ──────────────

export function masteryColor(score: number): string {
  if (score >= 85) return "text-emerald-400";
  if (score >= 70) return "text-green-400";
  if (score >= 50) return "text-amber-400";
  if (score >= 30) return "text-orange-400";
  return "text-red-400";
}

export function masteryBgColor(score: number): string {
  if (score >= 85) return "bg-emerald-500/15 border-emerald-500/30";
  if (score >= 70) return "bg-green-500/15 border-green-500/30";
  if (score >= 50) return "bg-amber-500/15 border-amber-500/30";
  if (score >= 30) return "bg-orange-500/15 border-orange-500/30";
  return "bg-red-500/15 border-red-500/30";
}

export function statusLabel(status: MasteryStatus | string): string {
  const map: Record<string, string> = {
    not_started: "Not Started",
    in_progress: "In Progress",
    mastered: "Mastered",
    needs_review: "Needs Review",
    NOT_STARTED: "Not Started",
    VERY_WEAK: "Very Weak",
    WEAK: "Weak",
    DEVELOPING: "Developing",
    PROFICIENT: "Proficient",
    MASTERED: "Mastered",
  };
  return map[status] || status;
}

function _mapState(state: string): MasteryStatus {
  const map: Record<string, MasteryStatus> = {
    NOT_STARTED: "not_started",
    VERY_WEAK: "needs_review",
    WEAK: "needs_review",
    DEVELOPING: "in_progress",
    PROFICIENT: "in_progress",
    MASTERED: "mastered",
    mastered: "mastered",
    in_progress: "in_progress",
    needs_review: "needs_review",
    not_started: "not_started",
  };
  return map[state] || "not_started";
}

// Legacy sync stubs — now return empty defaults; components should use async fetch* versions
export function getMastery(_conceptId: string): Mastery | undefined { return undefined; }
export function getAllMastery(): Mastery[] { return []; }
export function getWeakConcepts(): Mastery[] { return []; }
export function getRecommendedConcept(): string { return ""; }
export function getLearningPath(): LearningPathItem[] { return []; }
export function getProgressStats() { return {}; }
