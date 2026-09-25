import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi } from "vitest";

import { PlayerProfileContent } from "./PlayerProfileContent";

vi.mock("@/api/generated/endpoints", () => ({
  useUsersRetrieveSuspense: () => ({
    data: {
      id: 2,
      name: "Alice",
      picture: null,
      createdAt: "2025-01-15T12:00:00Z",
      totalGames: 28,
      soloWins: 2,
      draws: 5,
      losses: 11,
      nmrRate: 0.125,
      cdRate: 0,
      reliabilityTier: "reliable",
      commitment: "high",
    },
  }),
}));

const getRow = (label: string) => screen.getByText(label).closest("div")!;

describe("PlayerProfileContent", () => {
  it("shows the commitment tier only as the badge", () => {
    render(<PlayerProfileContent userId={2} />);

    expect(
      screen.getByRole("button", { name: "Commitment: High" })
    ).toBeInTheDocument();
    expect(screen.queryByText("Tier")).not.toBeInTheDocument();
  });

  it("renders the NMR rate as a percentage under Commitment", () => {
    render(<PlayerProfileContent userId={2} />);

    const section = screen
      .getByRole("heading", { name: "Commitment" })
      .closest("section")!;
    expect(within(section).getByText("NMR rate")).toBeInTheDocument();
    expect(within(section).getByText("13%")).toBeInTheDocument();
  });

  it.each([
    ["Total games", "28"],
    ["Solo wins", "2"],
    ["Draws", "5"],
    ["Losses", "11"],
  ])("renders %s as %s", (label, value) => {
    render(<PlayerProfileContent userId={2} />);

    expect(within(getRow(label)).getByText(value)).toBeInTheDocument();
  });

  it("explains the NMR rate when the info button is tapped", async () => {
    const user = userEvent.setup();
    render(<PlayerProfileContent userId={2} />);

    await user.click(screen.getByRole("button", { name: "What is NMR rate?" }));

    expect(
      screen.getByText(/percentage of movement phases/i)
    ).toBeInTheDocument();
  });
});
