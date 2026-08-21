/**
 * Adaptive Engine client.
 * Every adaptive value here comes from the backend adaptive services
 * (LexiMind Mastery Score, weak concepts, recommendations, learning path).
 * Nothing on this page is randomised or hardcoded.
 */
import { useEffect, useState } from "react";
import type { LearningPathItemStatus, MasteryStatus, User } from "../types/education";
import {
  getMasteryApi, getWeakConceptsApi, getLearningPathApi, getProgressApi,
  getNextRecommendationApi, getDailyPlanApi, getReviewScheduleApi,
} from "../lib/api";
import { loadUser } from "../store/userStore";

export const FALLBACK_USER_ID = "demo-user-1";
export const FALLBACK_SUBJECT_ID = "em1-btech";

export interface MasteryRow {
  userId: string;
  conceptId: string;
  concept: string;
  score: number;
  mastery: number;
  state: string;
  status: MasteryStatus;
  questionsAttempted: number;
  questionsCorrect: number;
  questionsIncorrect: number;
  streak: number;
  lastAttempted?: string | null;
  nextReviewAt?: string | null;
  confidence: number;
}

export interface WeakConcept {
  conceptId: string;
  concept: string;
  subjectId?: string;
  subject?: string;
  chapter?: string;
  mastery: number;
  state: string;
  reason: string;
  reasons: string[];
  weakPrerequisites: { conceptId: string; concept: string; mastery: number; attempted: number }[];
}

export interface Recommendation {
  type: "LEARN" | "REVIEW" | "PRACTICE" | "PYQ" | "QUIZ";
  conceptId: string;
  concept: string;
  subjectId?: string;
  subject?: string;
  chapterId?: string;
  chapter?: string;
  title: string;
  reason: string;
  estimatedMinutes: number;
  priority: number;
  mastery: number;
  minutes?: number;
}

export interface DailyPlan {
  studyMinutes: number;
  plannedMinutes: number;
  blocks: Recommendation[];
  empty: boolean;
  message?: string | null;
}

export interface PathItem {
  id: string;
  conceptId: string;
  concept: string;
  status: "COMPLETED" | "CURRENT" | "RECOMMENDED" | "LOCKED" | "NEEDS_REVIEW";
  state: string;
  mastery: number;
  attempted: number;
  estimatedMinutes: number;
  isCurrentFocus: boolean;
  nextReviewAt?: string | null;
  note?: string | null;
}

/** Current user id — the backend scopes every adaptive record by this. */
export function currentUser(): User | null {
  return loadUser();
}

export function currentUserId(user?: User | null): string {
  return (user ?? loadUser())?.id || FALLBACK_USER_ID;
}

export function currentSubjectId(user?: User | null): string {
  return (user ?? loadUser())?.academicProfile?.subjectIds?.[0] || FALLBACK_SUBJECT_ID;
}

/** Backend learning-path states → the UI's existing status vocabulary. */
export function pathStatusToUi(status: string): LearningPathItemStatus {
  switch ((status || "").toUpperCase()) {
    case "COMPLETED": return "mastered";
    case "NEEDS_REVIEW": return "needs_review";
    case "CURRENT": return "in_progress";
    case "LOCKED": return "locked";
    default: return "available";
  }
}

export async function fetchMastery(userId: string): Promise<MasteryRow[]> {
  const r = await getMasteryApi(userId);
  return r.data ?? [];
}

export async function fetchWeakConcepts(userId: string, subjectId?: string): Promise<WeakConcept[]> {
  const r = await getWeakConceptsApi(userId, subjectId);
  return r.data?.weakConcepts ?? [];
}

export async function fetchNextRecommendation(userId: string, subjectId?: string): Promise<Recommendation | null> {
  const r = await getNextRecommendationApi(userId, subjectId);
  return r.data?.recommendation ?? null;
}

export async function fetchDailyPlan(userId: string, subjectId?: string, minutes?: number): Promise<DailyPlan> {
  const r = await getDailyPlanApi(userId, subjectId, minutes);
  return r.data;
}

export async function fetchLearningPath(userId: string, subjectId: string): Promise<PathItem[]> {
  const r = await getLearningPathApi(userId, subjectId);
  return r.data?.items ?? [];
}

export async function fetchProgress(userId: string) {
  const r = await getProgressApi(userId);
  return r.data;
}

export async function fetchReviewSchedule(userId: string) {
  const r = await getReviewScheduleApi(userId);
  return r.data;
}

/** Small helper so pages can load adaptive data without repeating boilerplate. */
export function useAdaptive<T>(loader: () => Promise<T>, deps: unknown[], initial: T) {
  const [data, setData] = useState<T>(initial);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    loader()
      .then(d => { if (!cancelled) { setData(d); setError(null); } })
      .catch(e => { if (!cancelled) setError(e?.message || "Could not load data"); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  return { data, loading, error };
}

/** Mastery for the signed-in user, keyed by concept id. */
export function useMasteryMap() {
  const userId = currentUserId();
  const { data, loading, error } = useAdaptive<MasteryRow[]>(() => fetchMastery(userId), [userId], []);
  const map: Record<string, MasteryRow> = {};
  for (const row of data) map[row.conceptId] = row;
  return { map, rows: data, loading, error };
}

export function masteryColor(score: number): string {
  if (score >= 85) return "text-emerald-400";
  if (score >= 70) return "text-lime-400";
  if (score >= 50) return "text-amber-400";
  if (score >= 30) return "text-orange-400";
  return "text-red-400";
}

export function masteryBgColor(score: number): string {
  if (score >= 85) return "bg-emerald-500/15 border-emerald-500/30";
  if (score >= 70) return "bg-lime-500/15 border-lime-500/30";
  if (score >= 50) return "bg-amber-500/15 border-amber-500/30";
  if (score >= 30) return "bg-orange-500/15 border-orange-500/30";
  return "bg-red-500/15 border-red-500/30";
}

export function stateLabel(state: string): string {
  const map: Record<string, string> = {
    NOT_STARTED: "Not Started",
    VERY_WEAK: "Very Weak",
    WEAK: "Weak",
    DEVELOPING: "Developing",
    PROFICIENT: "Proficient",
    MASTERED: "Mastered",
  };
  return map[(state || "").toUpperCase()] ?? state;
}

export function statusLabel(status: MasteryStatus): string {
  const map: Record<MasteryStatus, string> = {
    not_started: "Not Started",
    in_progress: "In Progress",
    mastered: "Mastered",
    needs_review: "Needs Review",
  };
  return map[status];
}
