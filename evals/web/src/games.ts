import type { Feedback, GameEnd, GamePhase, Phase, Reference } from "./api";
import { mean, meanInterval, type Interval } from "./stats";

export const OVERALL = "overall";

export type Note = { key: string; heading: string; text: string };

export type TimelinePoint = { label: string; year: number | null; centres: Record<string, number> };

export type Band = { centres: number; share: number; interval: Interval | null; games: number };

const RESULTS: Record<string, string> = {
  OK: "Succeeded",
  ErrBounce: "Bounced",
  ErrSupportBroken: "Support cut",
  ErrInvalidSupporteeOrder: "Supported order not made",
  ErrIllegalSupportDestination: "Support to an unreachable province",
  ErrMissingConvoyPath: "No convoy path",
  ErrConvoyDislodged: "Convoy dislodged",
  ErrIllegalMove: "Illegal",
  ErrIllegalDestination: "Illegal destination",
  ErrInvalidDestination: "Invalid destination",
  ErrMissingUnit: "No unit",
  ErrMissingSupportUnit: "Supported unit missing",
};

const ENDS: Record<GameEnd, string> = {
  horizon: "Played to 1905",
  solo: "Solo",
  eliminated: "Eliminated",
};

export const phaseKey = (phase: Phase): string => `${phase.year}-${phase.season}-${phase.type}`;

export const phaseLabel = (phase: Phase): string => `${phase.season} ${phase.year} ${phase.type}`;

export const formatResult = (result: string | null): string =>
  result === null ? "Not resolved" : (RESULTS[result] ?? result);

export const succeeded = (result: string | null): boolean => result === null || result === "OK";

export const formatEnd = (end: GameEnd): string => ENDS[end];

export const formatShare = (share: number | null): string => (share === null ? "–" : `${share.toFixed(1)}%`);

export const formatCentres = (centres: number | null): string =>
  centres === null ? "–" : `${Number.isInteger(centres) ? centres : centres.toFixed(1)}`;

export const failed = (phase: GamePhase): boolean => Boolean(phase.answer?.problem);

export const mergeNotes = (feedback: Feedback, drafts: Record<string, string>): Feedback => {
  const phases = { ...feedback.phases };
  for (const [key, text] of Object.entries(drafts)) {
    if (key !== OVERALL) phases[key] = text;
  }
  return { overall: drafts[OVERALL] ?? feedback.overall, phases };
};

export const stitchNotes = (feedback: Feedback, phases: GamePhase[]): Note[] => {
  const notes: Note[] = [];
  if (feedback.overall.trim()) {
    notes.push({ key: OVERALL, heading: "Overall:", text: feedback.overall });
  }
  for (const phase of phases) {
    const text = feedback.phases[phase.key] ?? "";
    if (text.trim()) {
      notes.push({ key: phase.key, heading: `${phaseLabel(phase.phase)}:`, text });
    }
  }
  return notes;
};

const count = (supplyCenters: { nation: string }[], nations: string[]): Record<string, number> =>
  Object.fromEntries(nations.map(nation => [nation, supplyCenters.filter(center => center.nation === nation).length]));

export const centreTimeline = (phases: GamePhase[], finalCentres: Record<string, number>): TimelinePoint[] => {
  const nations = Object.keys(finalCentres).sort();
  const years = phases
    .filter(phase => phase.phase.season === "Spring" && phase.phase.type === "Movement")
    .map(phase => ({
      label: String(phase.phase.year),
      year: phase.phase.year,
      centres: count(phase.supply_centers, nations),
    }));
  return [...years, { label: "End", year: null, centres: finalCentres }];
};

export const firstPhaseOf = (phases: GamePhase[], year: number | null): GamePhase | undefined =>
  year === null ? phases[phases.length - 1] : phases.find(phase => phase.phase.year === year);

export const referenceBand = (reference: Reference): Band | null => {
  if (reference === null || reference.games.length === 0) return null;
  const shares = reference.games.map(game => game.share);
  return {
    centres: mean(reference.games.map(game => game.centres))!,
    share: mean(shares)!,
    interval: meanInterval(shares),
    games: reference.games.length,
  };
};

export const formatBand = (band: Band | null): string =>
  band === null
    ? "no reference"
    : `${formatCentres(band.centres)} centres · ${formatShare(band.share)}` +
      (band.interval ? ` (${band.interval.low.toFixed(1)}–${band.interval.high.toFixed(1)}%)` : "");
