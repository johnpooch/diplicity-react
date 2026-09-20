import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

vi.mock("firebase/app", () => ({
  initializeApp: () => ({}),
}));

vi.mock("firebase/messaging", () => ({
  deleteToken: vi.fn(),
  getMessaging: vi.fn(),
  getToken: vi.fn(),
  onMessage: vi.fn(),
  isSupported: vi.fn(),
}));

import { clearDeliveredNotifications } from "./messaging";

const setServiceWorker = (value: unknown) => {
  Object.defineProperty(navigator, "serviceWorker", {
    value,
    configurable: true,
  });
};

const notification = () => ({ close: vi.fn() });

describe("clearDeliveredNotifications", () => {
  beforeEach(() => {
    setServiceWorker(undefined);
  });

  afterEach(() => {
    Reflect.deleteProperty(navigator, "serviceWorker");
  });

  it("closes every delivered notification", async () => {
    const notifications = [notification(), notification()];
    setServiceWorker({
      getRegistration: vi.fn().mockResolvedValue({
        getNotifications: vi.fn().mockResolvedValue(notifications),
      }),
    });

    await clearDeliveredNotifications();

    expect(notifications[0].close).toHaveBeenCalledOnce();
    expect(notifications[1].close).toHaveBeenCalledOnce();
  });

  it("does nothing when there is no service worker registration", async () => {
    const getRegistration = vi.fn().mockResolvedValue(undefined);
    setServiceWorker({ getRegistration });

    await expect(clearDeliveredNotifications()).resolves.toBeUndefined();

    expect(getRegistration).toHaveBeenCalledOnce();
  });

  it("does nothing when service workers are unsupported", async () => {
    Reflect.deleteProperty(navigator, "serviceWorker");

    await expect(clearDeliveredNotifications()).resolves.toBeUndefined();
  });
});
