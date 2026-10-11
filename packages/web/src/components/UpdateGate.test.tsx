import { render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { UpdateGate } from "./UpdateGate";
import { APP_STORE_URL, PLAY_STORE_URL } from "@/constants";

const mockIsNativePlatform = vi.fn();
const mockIsIosPlatform = vi.fn();
const mockGetInfo = vi.fn();
const mockVersionRetrieve = vi.fn();
const mockHideSplashScreen = vi.fn();

vi.mock("@/utils/platform", () => ({
  isNativePlatform: () => mockIsNativePlatform(),
  isIosPlatform: () => mockIsIosPlatform(),
}));

vi.mock("@capacitor/app", () => ({
  App: { getInfo: () => mockGetInfo() },
}));

vi.mock("@capacitor/splash-screen", () => ({
  SplashScreen: { hide: () => mockHideSplashScreen() },
}));

vi.mock("@/api/generated/endpoints", async () => {
  const actual = await vi.importActual("@/api/generated/endpoints");
  return {
    ...actual,
    versionRetrieve: () => mockVersionRetrieve(),
  };
});

const renderUpdateGate = () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <UpdateGate>
        <div>App content</div>
      </UpdateGate>
    </QueryClientProvider>
  );
};

describe("UpdateGate", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockIsNativePlatform.mockReturnValue(true);
    mockIsIosPlatform.mockReturnValue(false);
    mockGetInfo.mockResolvedValue({ version: "1.5.8" });
    mockVersionRetrieve.mockResolvedValue({ minimumClientVersion: "0.0.0" });
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("renders children on web without checking the app version", () => {
    mockIsNativePlatform.mockReturnValue(false);
    renderUpdateGate();
    expect(screen.getByText("App content")).toBeInTheDocument();
    expect(mockGetInfo).not.toHaveBeenCalled();
  });

  it("renders children when the native version matches the minimum", async () => {
    mockVersionRetrieve.mockResolvedValue({
      minimumClientVersion: "1.5.8",
    });
    renderUpdateGate();
    expect(await screen.findByText("App content")).toBeInTheDocument();
  });

  it("renders children when the native version is above the minimum", async () => {
    mockGetInfo.mockResolvedValue({ version: "1.10.0" });
    mockVersionRetrieve.mockResolvedValue({
      minimumClientVersion: "1.9.0",
    });
    renderUpdateGate();
    expect(await screen.findByText("App content")).toBeInTheDocument();
  });

  it("blocks the app when the native version is below the minimum", async () => {
    mockVersionRetrieve.mockResolvedValue({
      minimumClientVersion: "1.6.0",
    });
    renderUpdateGate();
    expect(await screen.findByText("Update required")).toBeInTheDocument();
    expect(screen.queryByText("App content")).not.toBeInTheDocument();
  });

  it("links to the Play Store on Android", async () => {
    mockVersionRetrieve.mockResolvedValue({
      minimumClientVersion: "1.6.0",
    });
    renderUpdateGate();
    expect(await screen.findByRole("link", { name: "Update Diplicity" })).toHaveAttribute(
      "href",
      PLAY_STORE_URL
    );
  });

  it("links to the App Store on iOS", async () => {
    mockIsIosPlatform.mockReturnValue(true);
    mockVersionRetrieve.mockResolvedValue({
      minimumClientVersion: "1.6.0",
    });
    renderUpdateGate();
    expect(await screen.findByRole("link", { name: "Update Diplicity" })).toHaveAttribute(
      "href",
      APP_STORE_URL
    );
  });

  it("renders children when the version request fails", async () => {
    mockVersionRetrieve.mockRejectedValue(new Error("Network error"));
    renderUpdateGate();
    expect(await screen.findByText("App content")).toBeInTheDocument();
  });

  it("renders children when the version request never responds", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    mockVersionRetrieve.mockReturnValue(new Promise(() => {}));
    renderUpdateGate();
    await vi.advanceTimersByTimeAsync(5000);
    expect(await screen.findByText("App content")).toBeInTheDocument();
  });

  it("renders children when the native app info never arrives", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    mockGetInfo.mockReturnValue(new Promise(() => {}));
    renderUpdateGate();
    await waitFor(() => expect(mockGetInfo).toHaveBeenCalled());
    await vi.advanceTimersByTimeAsync(5000);
    expect(await screen.findByText("App content")).toBeInTheDocument();
  });

  it("keeps the splash screen up until the version check settles", async () => {
    let resolveVersion: (value: unknown) => void = () => {};
    mockVersionRetrieve.mockReturnValue(
      new Promise(resolve => {
        resolveVersion = resolve;
      })
    );
    renderUpdateGate();
    expect(mockHideSplashScreen).not.toHaveBeenCalled();
    resolveVersion({ minimumClientVersion: "0.0.0" });
    expect(await screen.findByText("App content")).toBeInTheDocument();
    expect(mockHideSplashScreen).toHaveBeenCalled();
  });

  it("hides the splash screen when the version check fails", async () => {
    mockVersionRetrieve.mockRejectedValue(new Error("Network error"));
    renderUpdateGate();
    await screen.findByText("App content");
    expect(mockHideSplashScreen).toHaveBeenCalled();
  });

  it("hides the splash screen when the app must be updated", async () => {
    mockVersionRetrieve.mockResolvedValue({ minimumClientVersion: "1.6.0" });
    renderUpdateGate();
    await screen.findByText("Update required");
    expect(mockHideSplashScreen).toHaveBeenCalled();
  });
});
