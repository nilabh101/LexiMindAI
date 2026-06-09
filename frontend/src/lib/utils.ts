import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatNumber(n: number): string {
  return new Intl.NumberFormat().format(n);
}

export function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function gradeToLabel(grade: number): string {
  if (grade <= 6) return "Elementary";
  if (grade <= 9) return "Middle School";
  if (grade <= 12) return "High School";
  if (grade <= 16) return "College";
  return "Postgraduate";
}

export function sentimentColor(label: string): string {
  const map: Record<string, string> = {
    positive: "#22c55e",
    negative: "#ef4444",
    neutral: "#94a3b8",
    mixed: "#f59e0b",
  };
  return map[label] || "#94a3b8";
}

export function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}
