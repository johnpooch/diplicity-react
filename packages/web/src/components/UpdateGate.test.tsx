import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { UpdateGate } from "./UpdateGate";
import { APP_STORE_URL, PLAY_STORE_URL } from "@/constants";

const mockIsNativePlatform = vi.fn();
const mockIsIosPlatform = vi.fn();
const mockGetInfo = vi.fn();
const mockVersionRetrieve = vi.fn();

vi.mock("@/utils/platform", () => ({
  isNativePlatform: () => mockIsNativePlatform(),
  isIosPlatform: () => mockIsIosPlatform(),
}));

vi.mock("@capacitor/app", () => ({
  App: { getInfo: () => mockGetInfo() },
}));

vi.mock("@/api/generated/endpoints", async () => {
  const actual = await vi.importActual("@/api/generated/endpoints");
  return {
    ...actual,
    useVersionRetrieveSuspense: () => mockVersionRetrieve(),
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
    mockVersionRetrieve.mockReturnValue({
      data: { minimumClientVersion: "0.0.0" },
    });
  });

  it("renders children on web without checking the app version", () => {
    mockIsNativePlatform.mockReturnValue(false);
    renderUpdateGate();
    expect(screen.getByText("App content")).toBeInTheDocument();
    expect(mockGetInfo).not.toHaveBeenCalled();
  });

  it("renders children when the native version matches the minimum", async () => {
    mockVersionRetrieve.mockReturnValue({
      data: { minimumClientVersion: "1.5.8" },
    });
    renderUpdateGate();
    expect(await screen.findByText("App content")).toBeInTheDocument();
  });

  it("renders children when the native version is above the minimum", async () => {
    mockGetInfo.mockResolvedValue({ version: "1.10.0" });
    mockVersionRetrieve.mockReturnValue({
      data: { minimumClientVersion: "1.9.0" },
    });
    renderUpdateGate();
    expect(await screen.findByText("App content")).toBeInTheDocument();
  });

  it("blocks the app when the native version is below the minimum", async () => {
    mockVersionRetrieve.mockReturnValue({
      data: { minimumClientVersion: "1.6.0" },
    });
    renderUpdateGate();
    expect(await screen.findByText("Update required")).toBeInTheDocument();
    expect(screen.queryByText("App content")).not.toBeInTheDocument();
  });

  it("links to the Play Store on Android", async () => {
    mockVersionRetrieve.mockReturnValue({
      data: { minimumClientVersion: "1.6.0" },
    });
    renderUpdateGate();
    expect(await screen.findByRole("link", { name: "Update Diplicity" })).toHaveAttribute(
      "href",
      PLAY_STORE_URL
    );
  });

  it("links to the App Store on iOS", async () => {
    mockIsIosPlatform.mockReturnValue(true);
    mockVersionRetrieve.mockReturnValue({
      data: { minimumClientVersion: "1.6.0" },
    });
    renderUpdateGate();
    expect(await screen.findByRole("link", { name: "Update Diplicity" })).toHaveAttribute(
      "href",
      APP_STORE_URL
    );
  });

  it("renders children when the version request fails", () => {
    mockVersionRetrieve.mockImplementation(() => {
      throw new Error("Network error");
    });
    renderUpdateGate();
    expect(screen.getByText("App content")).toBeInTheDocument();
  });
});
