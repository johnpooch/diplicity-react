export type Interval = { low: number; high: number };

export type Tally = { answers: number; failed: number; reasonable: number };

const Z = 1.96;

export const usable = (tally: Tally): number => tally.answers - tally.failed;

export const wilson = (successes: number, trials: number): Interval | null => {
  if (trials === 0) return null;
  const share = successes / trials;
  const spread = (Z * Z) / trials;
  const centre = (share + spread / 2) / (1 + spread);
  const half = (Z * Math.sqrt((share * (1 - share)) / trials + spread / (4 * trials))) / (1 + spread);
  return { low: Math.max(0, centre - half), high: Math.min(1, centre + half) };
};

export const scoreInterval = (tally: Tally): Interval | null => wilson(tally.reasonable, usable(tally));

export const overlaps = (a: Interval, b: Interval): boolean => a.low <= b.high && b.low <= a.high;

export const mean = (values: number[]): number | null =>
  values.length === 0 ? null : values.reduce((total, value) => total + value, 0) / values.length;

export const meanInterval = (values: number[]): Interval | null => {
  const centre = mean(values);
  if (centre === null || values.length < 2) return null;
  const variance = values.reduce((total, value) => total + (value - centre) ** 2, 0) / (values.length - 1);
  const half = (Z * Math.sqrt(variance)) / Math.sqrt(values.length);
  return { low: centre - half, high: centre + half };
};
