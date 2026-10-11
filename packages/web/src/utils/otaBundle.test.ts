import { describe, it, expect, vi, beforeEach } from "vitest";

const current = vi.fn();
const getFailedUpdate = vi.fn();
const setTag = vi.fn();
const captureMessage = vi.fn();

vi.mock("@capgo/capacitor-updater", () => ({
  CapacitorUpdater: {
    current: () => current(),
    getFailedUpdate: () => getFailedUpdate(),
  },
}));

vi.mock("@sentry/react", () => ({
  setTag: (...args: unknown[]) => setTag(...args),
  captureMessage: (...args: unknown[]) => captureMessage(...args),
}));

import { reportOtaBundle } from "./otaBundle";

const bundle = (version: string) => ({
  id: "abc",
  version,
  downloaded: "",
  checksum: "",
  status: "success",
});

describe("reportOtaBundle", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    current.mockResolvedValue({ bundle: bundle("1.5.12.4"), native: "1.5.12" });
    getFailedUpdate.mockResolvedValue(null);
  });

  it("tags Sentry events with the running bundle version", async () => {
    await reportOtaBundle();

    expect(setTag).toHaveBeenCalledWith("ota_bundle", "1.5.12.4");
  });

  it("reports nothing when no bundle was rolled back", async () => {
    await reportOtaBundle();

    expect(captureMessage).not.toHaveBeenCalled();
  });

  it("reports a bundle the updater rolled back", async () => {
    getFailedUpdate.mockResolvedValue({ bundle: bundle("1.5.12.3") });

    await reportOtaBundle();

    expect(captureMessage).toHaveBeenCalledWith(
      "OTA bundle 1.5.12.3 was rolled back",
      "warning"
    );
  });

  it("swallows a failure from the updater", async () => {
    current.mockRejectedValue(new Error("not implemented"));
    const consoleError = vi.spyOn(console, "error").mockImplementation(() => {});

    await expect(reportOtaBundle()).resolves.toBeUndefined();

    expect(consoleError).toHaveBeenCalled();
    consoleError.mockRestore();
  });
});
