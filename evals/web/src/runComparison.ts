import type { RunDetail } from "./api";
import { overlaps, scoreInterval, usable, type Interval, type Tally } from "./stats";

export type Side = Tally & { score: number | null; interval: Interval | null };

export type Comparison = {
  fixtures: string[];
  here: Side;
  there: Side;
  overlapping: boolean | null;
};

export const sharedFixtures = (own: string[], other: string[]): string[] => own.filter(id => other.includes(id));

const side = (run: RunDetail, fixtures: string[]): Side => {
  const covered = run.fixtures.filter(fixture => fixtures.includes(fixture.id));
  const tally = {
    answers: covered.reduce((sum, fixture) => sum + fixture.answers, 0),
    failed: covered.reduce((sum, fixture) => sum + fixture.failed, 0),
    reasonable: covered.reduce((sum, fixture) => sum + fixture.reasonable, 0),
  };
  const trials = usable(tally);
  return { ...tally, score: trials ? tally.reasonable / trials : null, interval: scoreInterval(tally) };
};

export const compareRuns = (run: RunDetail, other: RunDetail): Comparison | null => {
  const fixtures = sharedFixtures(
    run.fixtures.map(fixture => fixture.id),
    other.fixtures.map(fixture => fixture.id)
  );
  if (fixtures.length === 0) return null;
  const here = side(run, fixtures);
  const there = side(other, fixtures);
  return {
    fixtures,
    here,
    there,
    overlapping: here.interval && there.interval ? overlaps(here.interval, there.interval) : null,
  };
};
