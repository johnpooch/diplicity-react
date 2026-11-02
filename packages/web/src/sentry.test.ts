import { describe, it, expect, vi, beforeEach } from "vitest";
import type { ErrorEvent } from "@sentry/react";

const init = vi.fn();

vi.mock("@sentry/react", () => ({
  init: (...args: unknown[]) => init(...args),
  browserTracingIntegration: vi.fn(),
  replayIntegration: vi.fn(),
}));

import { initializeSentry } from "./sentry";

const beforeSend = (event: ErrorEvent) => {
  initializeSentry();
  return init.mock.calls[0][0].beforeSend(event, {});
};

const eventWithFrames = (filenames: string[]): ErrorEvent => ({
  type: undefined,
  exception: {
    values: [
      {
        type: "Error",
        value: "oa",
        stacktrace: { frames: filenames.map(filename => ({ filename })) },
      },
    ],
  },
});

describe("initializeSentry beforeSend", () => {
  beforeEach(() => {
    init.mockReset();
    vi.stubEnv("VITE_SENTRY_DSN", "https://key@sentry.example/1");
    vi.spyOn(console, "log").mockImplementation(() => {});
  });

  it("drops errors with a frame from the Google sign-in script", () => {
    const event = eventWithFrames([
      "https://accounts.google.com/gsi/client",
      "https://diplicity.com/assets/vendor-observability-abc123.js",
    ]);

    expect(beforeSend(event)).toBeNull();
  });

  it("keeps errors without a frame from the Google sign-in script", () => {
    const event = eventWithFrames([
      "https://diplicity.com/assets/vendor-observability-abc123.js",
    ]);

    expect(beforeSend(event)).toBe(event);
  });

  it("removes the Authorization header from kept events", () => {
    const event: ErrorEvent = {
      type: undefined,
      request: { headers: { Authorization: "Token secret", Accept: "*/*" } },
    };

    expect(beforeSend(event)?.request?.headers).toEqual({ Accept: "*/*" });
  });
});
