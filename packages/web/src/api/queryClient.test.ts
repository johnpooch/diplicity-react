import { focusManager } from "@tanstack/react-query";
import { afterEach, describe, expect, it, vi } from "vitest";

const isNativePlatform = vi.fn();
const addListener = vi.fn();

vi.mock("../utils/platform", () => ({
  isNativePlatform: () => isNativePlatform(),
}));

vi.mock("@capacitor/app", () => ({
  App: { addListener: (...args: unknown[]) => addListener(...args) },
}));

const loadQueryClient = async () => {
  vi.resetModules();
  await import("./queryClient");
};

describe("queryClient focus tracking", () => {
  afterEach(() => {
    focusManager.setFocused(undefined);
    vi.clearAllMocks();
  });

  it("follows the native app state on native platforms", async () => {
    isNativePlatform.mockReturnValue(true);
    addListener.mockReturnValue(Promise.resolve({ remove: vi.fn() }));
    const unsubscribe = focusManager.subscribe(() => {});

    await loadQueryClient();
    const [event, handler] = addListener.mock.lastCall as [
      string,
      (state: { isActive: boolean }) => void,
    ];

    expect(event).toBe("appStateChange");
    handler({ isActive: false });
    expect(focusManager.isFocused()).toBe(false);
    handler({ isActive: true });
    expect(focusManager.isFocused()).toBe(true);
    unsubscribe();
  });

  it("does not listen for native app state on the web", async () => {
    isNativePlatform.mockReturnValue(false);

    await loadQueryClient();

    expect(addListener).not.toHaveBeenCalled();
  });
});
