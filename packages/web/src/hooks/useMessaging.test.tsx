import React from "react";
import { act, renderHook } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useMessaging } from "./useMessaging";

type PushCallback = (payload: unknown) => void;
type NativePushCallback = (gameId: string | undefined) => void;

const pushListener: { web?: PushCallback; native?: NativePushCallback } = {};
const mockIsNativePlatform = vi.fn();

vi.mock("@/messaging", () => ({
  onMessageReceived: (callback: PushCallback) => {
    pushListener.web = callback;
    return () => {};
  },
  getToken: vi.fn(),
  registerServiceWorker: vi.fn(),
}));

vi.mock("@/messaging-native", () => ({
  checkPermission: () => Promise.resolve("granted"),
  addTokenRefreshListener: () => Promise.resolve({ remove: vi.fn() }),
  addNotificationReceivedListener: (callback: NativePushCallback) => {
    pushListener.native = callback;
    return Promise.resolve({ remove: vi.fn() });
  },
}));

vi.mock("@/utils/platform", () => ({
  isNativePlatform: () => mockIsNativePlatform(),
  isIosPlatform: () => false,
}));

vi.mock("@/auth", () => ({
  useAuth: () => ({ loggedIn: true }),
}));

vi.mock("@/api/generated/endpoints", async importOriginal => ({
  ...(await importOriginal<typeof import("@/api/generated/endpoints")>()),
  useDevicesList: () => ({ data: [] }),
  useDevicesCreate: () => ({ mutateAsync: vi.fn() }),
}));

const cachedKeys = [
  ["/game/game-1/"],
  ["/game/game-1/phase/3/"],
  ["/games/game-1/channel-previews/"],
  ["/game/game-2/"],
  ["/games/game-2/channel-previews/"],
  ["/games/mine/current/"],
  ["/games/mine/finished/", "infinite"],
  ["/games/", { page: 1 }],
  ["/user/"],
];

const renderMessaging = () => {
  const client = new QueryClient();
  cachedKeys.forEach(queryKey => client.setQueryData(queryKey, {}));
  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={client}>{children}</QueryClientProvider>
  );
  renderHook(() => useMessaging(), { wrapper });
  const invalidated = () =>
    cachedKeys
      .filter(queryKey => client.getQueryState(queryKey)?.isInvalidated)
      .map(([path]) => path);
  return { invalidated };
};

beforeEach(() => {
  pushListener.web = undefined;
  pushListener.native = undefined;
  mockIsNativePlatform.mockReset();
});

describe("useMessaging foreground push", () => {
  it("invalidates only the pushed game and the user's game lists on web", () => {
    mockIsNativePlatform.mockReturnValue(false);
    const { invalidated } = renderMessaging();

    act(() => pushListener.web?.({ data: { game_id: "game-1" } }));

    expect(invalidated()).toEqual([
      "/game/game-1/",
      "/game/game-1/phase/3/",
      "/games/game-1/channel-previews/",
      "/games/mine/current/",
      "/games/mine/finished/",
    ]);
  });

  it("invalidates only the pushed game and the user's game lists on native", () => {
    mockIsNativePlatform.mockReturnValue(true);
    const { invalidated } = renderMessaging();

    act(() => pushListener.native?.("game-2"));

    expect(invalidated()).toEqual([
      "/game/game-2/",
      "/games/game-2/channel-previews/",
      "/games/mine/current/",
      "/games/mine/finished/",
    ]);
  });

  it("invalidates every query when the push names no game", () => {
    mockIsNativePlatform.mockReturnValue(false);
    const { invalidated } = renderMessaging();

    act(() => pushListener.web?.({ data: {} }));

    expect(invalidated()).toEqual(cachedKeys.map(([path]) => path));
  });
});
