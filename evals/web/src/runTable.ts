import type { RunSummary } from "./api";
import { scoreInterval } from "./stats";

export type SortKey = "created" | "model" | "prompt" | "fixtures" | "score" | "answers";

export type Direction = "asc" | "desc";

const VALUES: Record<SortKey, (run: RunSummary) => string | number | null> = {
  created: run => run.created,
  model: run => run.model,
  prompt: run => run.prompt,
  fixtures: run => run.fixture_ids.length,
  score: run => scoreInterval(run)?.low ?? null,
  answers: run => run.answers,
};

export const SORT_KEYS = Object.keys(VALUES) as SortKey[];

export const firstDirection = (key: SortKey): Direction => (key === "model" || key === "prompt" ? "asc" : "desc");

export const sortRuns = (runs: RunSummary[], key: SortKey, direction: Direction): RunSummary[] => {
  const value = VALUES[key];
  return [...runs].sort((a, b) => {
    const left = value(a);
    const right = value(b);
    if (left === right) return b.created.localeCompare(a.created);
    if (left === null) return 1;
    if (right === null) return -1;
    const order = left < right ? -1 : 1;
    return direction === "asc" ? order : -order;
  });
};
