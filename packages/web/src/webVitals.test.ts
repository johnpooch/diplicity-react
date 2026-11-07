import { beforeEach, describe, expect, it, vi } from "vitest";

const spans: { name: string; options: unknown; end: ReturnType<typeof vi.fn> }[] =
  [];

vi.mock("@opentelemetry/api", () => ({
  trace: {
    getTracer: () => ({
      startSpan: (name: string, options: unknown) => {
        const span = { name, options, end: vi.fn() };
        spans.push(span);
        return span;
      },
    }),
  },
}));

const handlers: Record<string, (metric: unknown) => void> = {};
vi.mock("web-vitals", () => {
  const register = (name: string) => (cb: (metric: unknown) => void) => {
    handlers[name] = cb;
  };
  return {
    onLCP: register("LCP"),
    onINP: register("INP"),
    onCLS: register("CLS"),
    onFCP: register("FCP"),
    onTTFB: register("TTFB"),
  };
});

const isNativePlatform = vi.fn();
vi.mock("./utils/platform", () => ({
  isNativePlatform: () => isNativePlatform(),
}));

describe("webVitals", () => {
  beforeEach(() => {
    spans.length = 0;
    isNativePlatform.mockReset();
    vi.resetModules();
  });

  it("emits one span per metric with its value and rating", async () => {
    isNativePlatform.mockReturnValue(false);
    const { reportWebVitals } = await import("./webVitals");

    reportWebVitals();
    handlers.LCP({
      name: "LCP",
      value: 1800,
      delta: 1800,
      rating: "good",
      navigationType: "navigate",
      id: "v5-1",
    });

    expect(spans).toHaveLength(1);
    expect(spans[0].name).toBe("web_vital.LCP");
    expect(spans[0].options).toMatchObject({
      attributes: {
        "web_vital.name": "LCP",
        "web_vital.value": 1800,
        "web_vital.rating": "good",
        "app.platform": "web",
      },
    });
    expect(spans[0].end).toHaveBeenCalled();
  });

  it("registers all five metrics", async () => {
    isNativePlatform.mockReturnValue(false);
    const { reportWebVitals } = await import("./webVitals");

    reportWebVitals();

    expect(Object.keys(handlers).sort()).toEqual([
      "CLS",
      "FCP",
      "INP",
      "LCP",
      "TTFB",
    ]);
  });

  it("does not report app launch on the web", async () => {
    isNativePlatform.mockReturnValue(false);
    const { reportAppLaunch } = await import("./webVitals");

    reportAppLaunch();

    expect(spans).toHaveLength(0);
  });

  it("reports app launch once on native", async () => {
    isNativePlatform.mockReturnValue(true);
    const { reportAppLaunch } = await import("./webVitals");

    reportAppLaunch();
    reportAppLaunch();

    expect(spans).toHaveLength(1);
    expect(spans[0].name).toBe("app_launch");
    expect(spans[0].options).toMatchObject({
      attributes: { "app.platform": "native" },
    });
  });
});
