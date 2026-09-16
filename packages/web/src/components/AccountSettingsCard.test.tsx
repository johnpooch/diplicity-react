import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router";
import { describe, it, expect, vi, beforeEach } from "vitest";

import { AccountSettingsCard } from "./AccountSettingsCard";

if (!Element.prototype.hasPointerCapture) {
  Element.prototype.hasPointerCapture = () => false;
}
if (!Element.prototype.releasePointerCapture) {
  Element.prototype.releasePointerCapture = () => {};
}
if (!Element.prototype.scrollIntoView) {
  Element.prototype.scrollIntoView = () => {};
}

const mockSetPreference = vi.fn();
const mockEnableMessaging = vi.fn();
const mockDisableMessaging = vi.fn();
const mockNavigate = vi.fn();

let mockMessagingState = {
  enabled: false,
  permissionDenied: false,
  error: null as string | null,
};

vi.mock("@/theme/useTheme", () => ({
  useTheme: () => ({
    preference: "system",
    resolvedTheme: "light",
    setPreference: mockSetPreference,
  }),
}));

vi.mock("@/hooks/useMessaging", () => ({
  useMessaging: () => ({
    enableMessaging: mockEnableMessaging,
    disableMessaging: mockDisableMessaging,
    ...mockMessagingState,
  }),
}));

vi.mock("react-router", async importOriginal => {
  const actual = await importOriginal<typeof import("react-router")>();
  return { ...actual, useNavigate: () => mockNavigate };
});

const renderCard = () =>
  render(
    <MemoryRouter>
      <AccountSettingsCard />
    </MemoryRouter>
  );

describe("AccountSettingsCard", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockMessagingState = {
      enabled: false,
      permissionDenied: false,
      error: null,
    };
  });

  it("renders Appearance as a radio group with three options", () => {
    renderCard();

    expect(screen.getByText("Appearance")).toBeInTheDocument();
    const radios = screen.getAllByRole("radio");
    expect(radios).toHaveLength(3);
    expect(screen.getByLabelText("Light")).toBeInTheDocument();
    expect(screen.getByLabelText("Dark")).toBeInTheDocument();
    expect(screen.getByLabelText("System")).toBeInTheDocument();
  });

  it("updates the theme preference when a radio option is selected", async () => {
    const user = userEvent.setup();
    renderCard();

    await user.click(screen.getByLabelText("Dark"));

    expect(mockSetPreference).toHaveBeenCalledWith("dark");
  });

  it("shows a red warning when notifications are off", () => {
    renderCard();

    expect(screen.getByRole("switch")).not.toBeChecked();
    expect(
      screen.getByText(
        "You won't be informed if someone messages you or a game proceeds."
      )
    ).toHaveClass("text-destructive");
  });

  it("hides the warning when notifications are on", () => {
    mockMessagingState = { ...mockMessagingState, enabled: true };
    renderCard();

    expect(screen.getByRole("switch")).toBeChecked();
    expect(
      screen.queryByText(
        "You won't be informed if someone messages you or a game proceeds."
      )
    ).not.toBeInTheDocument();
  });

  it("enables push notifications when the switch is turned on", async () => {
    const user = userEvent.setup();
    renderCard();

    await user.click(screen.getByRole("switch"));

    expect(mockEnableMessaging).toHaveBeenCalled();
  });

  it("disables push notifications when the switch is turned off", async () => {
    mockMessagingState = { ...mockMessagingState, enabled: true };
    const user = userEvent.setup();
    renderCard();

    await user.click(screen.getByRole("switch"));

    expect(mockDisableMessaging).toHaveBeenCalled();
  });

  it("renders a small red Danger Zone header with an outlined red delete button", () => {
    renderCard();

    const header = screen.getByText("Danger Zone");
    expect(header).toHaveClass("text-destructive");
    expect(header.tagName).toBe("H2");

    const deleteButton = screen.getByRole("button", { name: "Delete Account" });
    expect(deleteButton).toHaveClass("text-destructive", "border-destructive");
  });

  it("navigates to delete-account when Delete Account is clicked", async () => {
    const user = userEvent.setup();
    renderCard();

    await user.click(screen.getByRole("button", { name: "Delete Account" }));

    expect(mockNavigate).toHaveBeenCalledWith("/delete-account");
  });
});
