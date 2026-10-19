import { describe, expect, test } from "vitest";
import { mean, meanInterval, overlaps, scoreInterval, wilson } from "./stats";

const percent = (value: number) => Math.round(value * 100);

describe("wilson", () => {
  test("eleven of thirty spans roughly 22 to 54 percent", () => {
    const interval = wilson(11, 30)!;
    expect([percent(interval.low), percent(interval.high)]).toEqual([22, 54]);
  });

  test("a single reasonable answer is far from certain", () => {
    const interval = wilson(1, 1)!;
    expect([percent(interval.low), percent(interval.high)]).toEqual([21, 100]);
  });

  test("none of thirty still leaves room above zero", () => {
    const interval = wilson(0, 30)!;
    expect(interval.low).toBe(0);
    expect(percent(interval.high)).toBe(11);
  });

  test("more answers narrow the interval", () => {
    const few = wilson(15, 30)!;
    const many = wilson(150, 300)!;
    expect(many.high - many.low).toBeLessThan(few.high - few.low);
  });

  test("no answers give no interval", () => {
    expect(wilson(0, 0)).toBeNull();
  });
});

describe("scoreInterval", () => {
  test("failed answers are left out of the trials", () => {
    expect(scoreInterval({ answers: 100, failed: 6, reasonable: 23 })).toEqual(wilson(23, 94));
  });
});

describe("overlaps", () => {
  test("touching intervals overlap and separate ones do not", () => {
    expect(overlaps({ low: 0.2, high: 0.5 }, { low: 0.5, high: 0.7 })).toBe(true);
    expect(overlaps({ low: 0.2, high: 0.4 }, { low: 0.5, high: 0.7 })).toBe(false);
  });
});

describe("meanInterval", () => {
  test("spans 1.96 standard errors either side of the mean", () => {
    const interval = meanInterval([10, 12, 14, 16])!;
    const half = (1.96 * Math.sqrt(20 / 3)) / 2;
    expect(interval.low).toBeCloseTo(13 - half);
    expect(interval.high).toBeCloseTo(13 + half);
  });

  test("identical values leave no spread", () => {
    expect(meanInterval([5, 5, 5])).toEqual({ low: 5, high: 5 });
  });

  test("one value has a mean but no interval", () => {
    expect(mean([7])).toBe(7);
    expect(meanInterval([7])).toBeNull();
  });

  test("no values have neither", () => {
    expect(mean([])).toBeNull();
    expect(meanInterval([])).toBeNull();
  });
});
