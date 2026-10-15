import { describe, expect, test } from "vitest";
import { overlaps, scoreInterval, wilson } from "./stats";

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
