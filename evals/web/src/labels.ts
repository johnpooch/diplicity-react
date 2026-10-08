import type { Label } from "./api";

export const LABELS: { label: Label; name: string; key: string; dot: string; active: string }[] = [
  {
    label: "reasonable",
    name: "Reasonable",
    key: "R",
    dot: "bg-emerald-600",
    active: "border-emerald-600 bg-emerald-600 text-white hover:bg-emerald-600/90 hover:text-white",
  },
  {
    label: "unreasonable",
    name: "Unreasonable",
    key: "U",
    dot: "bg-destructive",
    active: "border-destructive bg-destructive text-white hover:bg-destructive/90 hover:text-white",
  },
];

export const formatScore = (score: number | null): string =>
  score === null ? "–" : `${Math.round(score * 100)}%`;

export const formatRun = (created: string): string =>
  new Date(created).toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });

export const UNMARKED = { name: "Unmarked", dot: "bg-muted-foreground/40" };

export const plural = (count: number, noun: string): string => `${count} ${noun}${count === 1 ? "" : "s"}`;
