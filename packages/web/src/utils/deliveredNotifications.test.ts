import { describe, it, expect, vi, beforeEach } from "vitest";

const isNativePlatform = vi.fn();
const clearNative = vi.fn();
const clearWeb = vi.fn();

vi.mock("@/utils/platform", () => ({
  isNativePlatform: () => isNativePlatform(),
}));

vi.mock("@/messaging-native", () => ({
  clearDeliveredNotifications: () => clearNative(),
}));

vi.mock("@/messaging", () => ({
  clearDeliveredNotifications: () => clearWeb(),
}));

import { clearDeliveredNotifications } from "./deliveredNotifications";

describe("clearDeliveredNotifications", () => {
  beforeEach(() => {
    isNativePlatform.mockReset();
    clearNative.mockReset().mockResolvedValue(undefined);
    clearWeb.mockReset().mockResolvedValue(undefined);
  });

  it("clears via the native plugin on a native platform", async () => {
    isNativePlatform.mockReturnValue(true);

    await clearDeliveredNotifications();

    expect(clearNative).toHaveBeenCalledOnce();
    expect(clearWeb).not.toHaveBeenCalled();
  });

  it("clears via the service worker on the web", async () => {
    isNativePlatform.mockReturnValue(false);

    await clearDeliveredNotifications();

    expect(clearWeb).toHaveBeenCalledOnce();
    expect(clearNative).not.toHaveBeenCalled();
  });

  it("swallows a failure from the platform implementation", async () => {
    isNativePlatform.mockReturnValue(true);
    clearNative.mockRejectedValue(new Error("not available"));
    const consoleError = vi.spyOn(console, "error").mockImplementation(() => {});

    await expect(clearDeliveredNotifications()).resolves.toBeUndefined();

    expect(consoleError).toHaveBeenCalled();
    consoleError.mockRestore();
  });
});
