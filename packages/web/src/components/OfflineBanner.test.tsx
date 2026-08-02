import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { OfflineBanner } from "./OfflineBanner";

const mockUseNetworkStatus = vi.fn();

vi.mock("@/hooks", () => ({
  useNetworkStatus: () => mockUseNetworkStatus(),
}));

describe("OfflineBanner", () => {
  beforeEach(() => {
    mockUseNetworkStatus.mockReset();
  });

  it("shows the offline message when offline", () => {
    mockUseNetworkStatus.mockReturnValue(false);
    render(<OfflineBanner />);
    expect(screen.getByText("No internet connection")).toBeInTheDocument();
  });

  it("renders nothing when online", () => {
    mockUseNetworkStatus.mockReturnValue(true);
    const { container } = render(<OfflineBanner />);
    expect(container).toBeEmptyDOMElement();
  });
});
