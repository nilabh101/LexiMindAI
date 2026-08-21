/**
 * User / onboarding state store using localStorage.
 * Phase 1: local state only. Phase 2 will sync to backend.
 */
import { useState, useEffect } from "react";
import type { User, AcademicProfile, StudyGoal } from "../types/education";
import { DEMO_USER } from "../data/demoData";

const STORAGE_KEY = "leximind_user";
const ONBOARDING_KEY = "leximind_onboarding";

export interface OnboardingState {
  step: number;
  educationLevel?: "school" | "college";
  year?: number;
  courseId?: string;
  streamId?: string;
  subjectIds: string[];
  studyGoal?: StudyGoal;
  dailyMinutes?: number;
  name?: string;
  email?: string;
}

export function loadUser(): User | null {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    return JSON.parse(raw) as User;
  } catch {
    return null;
  }
}

export function saveUser(user: User): void {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(user));
}

export function clearUser(): void {
  localStorage.removeItem(STORAGE_KEY);
  localStorage.removeItem(ONBOARDING_KEY);
}

export function loadOnboarding(): OnboardingState {
  try {
    const raw = localStorage.getItem(ONBOARDING_KEY);
    if (!raw) return { step: 1, subjectIds: [] };
    return JSON.parse(raw) as OnboardingState;
  } catch {
    return { step: 1, subjectIds: [] };
  }
}

export function saveOnboarding(state: OnboardingState): void {
  localStorage.setItem(ONBOARDING_KEY, JSON.stringify(state));
}

export function completeOnboarding(onboarding: OnboardingState): User {
  const user: User = {
    id: `user-${Date.now()}`,
    name: onboarding.name || "Student",
    email: onboarding.email || "",
    createdAt: new Date().toISOString(),
    onboardingComplete: true,
    studyGoal: onboarding.studyGoal || "master_concepts",
    dailyStudyMinutes: onboarding.dailyMinutes || 60,
    streak: 0,
    academicProfile: {
      educationLevel: onboarding.educationLevel || "college",
      year: onboarding.year || 1,
      courseId: onboarding.courseId || "",
      streamId: onboarding.streamId,
      subjectIds: onboarding.subjectIds,
    },
  };
  saveUser(user);
  return user;
}

/** Use this during development to get a demo user instantly */
export function useDemoUser(): User {
  return DEMO_USER;
}
