/**
 * Adaptive Engine Service Interface
 * Phase 1: stub implementations that return demo data.
 * Phase 2: connect to real ML backend.
 */
import type { Mastery, LearningPathItem, MasteryStatus } from "../types/education";
import {
  DEMO_MASTERY, DEMO_LEARNING_PATH, DEMO_PROGRESS
} from "../data/demoData";
import { CONCEPTS } from "../data/curriculum";

export function getMastery(conceptId: string): Mastery | undefined {
  return DEMO_MASTERY.find(m => m.conceptId === conceptId);
}

export function getAllMastery(): Mastery[] {
  return DEMO_MASTERY;
}

export function getWeakConcepts(): Mastery[] {
  return DEMO_MASTERY.filter(m =>
    m.status === "needs_review" || (m.status === "in_progress" && m.score < 50)
  );
}

export function getRecommendedConcept(): string {
  const current = DEMO_LEARNING_PATH.find(i => i.isCurrentFocus);
  return current?.conceptId ?? DEMO_LEARNING_PATH[0]?.conceptId ?? "";
}

export function getLearningPath(): LearningPathItem[] {
  return DEMO_LEARNING_PATH;
}

export function getProgressStats() {
  return DEMO_PROGRESS;
}

/** Stub — will call POST /api/mastery/update in Phase 2 */
export async function updateMasteryAfterQuiz(
  conceptPerformances: { conceptId: string; correct: number; total: number }[]
): Promise<void> {
  console.log("[AdaptiveEngine] updateMastery stub:", conceptPerformances);
}

/** Stub — will call POST /api/learning-path/regenerate in Phase 2 */
export async function generateLearningPath(subjectId: string): Promise<LearningPathItem[]> {
  console.log("[AdaptiveEngine] generateLearningPath stub:", subjectId);
  return DEMO_LEARNING_PATH;
}

export function masteryColor(score: number): string {
  if (score >= 80) return "text-emerald-400";
  if (score >= 60) return "text-amber-400";
  if (score >= 30) return "text-orange-400";
  return "text-red-400";
}

export function masteryBgColor(score: number): string {
  if (score >= 80) return "bg-emerald-500/15 border-emerald-500/30";
  if (score >= 60) return "bg-amber-500/15 border-amber-500/30";
  if (score >= 30) return "bg-orange-500/15 border-orange-500/30";
  return "bg-red-500/15 border-red-500/30";
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
