import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { OfflineNotice } from "./OfflineNotice";

const mockUseNetworkStatus = vi.fn();

vi.mock("@/hooks", () => ({
  useNetworkStatus: () => mockUseNetworkStatus(),
}));

describe("OfflineNotice", () => {
  beforeEach(() => {
    mockUseNetworkStatus.mockReset();
    mockUseNetworkStatus.mockReturnValue(false);
  });

  it("retries when the user taps Try Again", async () => {
    const onRetry = vi.fn();
    render(<OfflineNotice onRetry={onRetry} />);

    await userEvent.click(screen.getByRole("button", { name: "Try Again" }));

    expect(onRetry).toHaveBeenCalledTimes(1);
  });

  it("retries automatically when the connection returns", () => {
    const onRetry = vi.fn();
    const { rerender } = render(<OfflineNotice onRetry={onRetry} />);
    expect(onRetry).not.toHaveBeenCalled();

    mockUseNetworkStatus.mockReturnValue(true);
    rerender(<OfflineNotice onRetry={onRetry} />);

    expect(onRetry).toHaveBeenCalledTimes(1);
  });

  it("does not retry when it mounts already online", () => {
    mockUseNetworkStatus.mockReturnValue(true);
    const onRetry = vi.fn();
    render(<OfflineNotice onRetry={onRetry} />);

    expect(onRetry).not.toHaveBeenCalled();
  });

  it("renders the full-screen variant heading", () => {
    render(<OfflineNotice onRetry={vi.fn()} fullScreen />);
    expect(
      screen.getByRole("heading", { name: "No internet connection" })
    ).toBeInTheDocument();
  });
});
