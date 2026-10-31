import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeAll, beforeEach, describe, expect, it, vi } from "vitest";
import type {
  CommitmentSquare,
  PublicUserProfile,
} from "@/api/generated/endpoints";
import { PlayerProfileContent } from "./PlayerProfileContent";

const square = (
  overrides: Partial<CommitmentSquare> = {}
): CommitmentSquare => ({
  anonymous: false,
  gameName: "Concert of Europe",
  submitted: 0,
  missed: 0,
  breakdown: [],
  points: 0,
  shade: "grey",
  ...overrides,
});

let profile: PublicUserProfile;

vi.mock("@/api/generated/endpoints", async importOriginal => ({
  ...(await importOriginal<typeof import("@/api/generated/endpoints")>()),
  useUsersRetrieveSuspense: () => ({ data: profile }),
}));

const buildProfile = (
  overrides: Partial<PublicUserProfile> = {}
): PublicUserProfile => ({
  id: 1,
  name: "Jane Doe",
  picture: null,
  createdAt: "2025-01-15T00:00:00Z",
  totalGames: 15,
  activeGames: 3,
  commitment: "high",
  commitmentTotal: 0,
  commitmentBand: "neutral",
  commitmentSquares: [],
  ...overrides,
});

const rowValue = (label: string) =>
  screen.getByText(label, { selector: "span" }).nextElementSibling?.textContent;

describe("PlayerProfileContent", () => {
  beforeAll(() => {
    globalThis.ResizeObserver = class {
      observe() {}
      unobserve() {}
      disconnect() {}
    };
  });

  beforeEach(() => {
    profile = buildProfile();
  });

  it("shows the profile and game counts", () => {
    render(<PlayerProfileContent userId={1} />);

    expect(
      screen.getByRole("heading", { name: "Jane Doe" })
    ).toBeInTheDocument();
    expect(screen.getByText(/Joined January 2025/)).toBeInTheDocument();
    expect(rowValue("Active")).toBe("3");
    expect(rowValue("Finished")).toBe("15");
  });

  it("summarises commitment across the player's games", () => {
    profile = buildProfile({
      commitmentTotal: 434,
      commitmentSquares: [
        square({ submitted: 98, missed: 1, points: 96, shade: "dark_green" }),
        square({
          submitted: 1,
          missed: 0,
          points: -9,
          shade: "red",
          breakdown: [
            { kind: "submitted", count: 1, points: 1 },
            { kind: "civil_disorder", count: 1, points: -10 },
          ],
        }),
      ],
    });

    render(<PlayerProfileContent userId={1} />);

    expect(rowValue("Commitment")).toBe("+434");
    expect(rowValue("Missed orders")).toBe("1%");
    expect(rowValue("Abandoned games")).toBe("1");
  });

  it("shows a negative total with a minus sign and no rate without phases", () => {
    profile = buildProfile({ commitmentTotal: -15 });

    render(<PlayerProfileContent userId={1} />);

    expect(rowValue("Commitment")).toBe("−15");
    expect(rowValue("Missed orders")).toBe("—");
  });

  it("shows the 48 most recent games in the grid", () => {
    profile = buildProfile({
      commitmentSquares: Array.from({ length: 50 }, (_, index) =>
        square({ gameName: `Game ${index}` })
      ),
    });

    render(<PlayerProfileContent userId={1} />);

    const squares = screen.getAllByRole("img");
    expect(squares).toHaveLength(48);
    expect(squares[0]).toHaveAccessibleName("Game 2: 0");
    expect(squares[47]).toHaveAccessibleName("Game 49: 0");
  });

  it("breaks down a game's points when its square is tapped", async () => {
    profile = buildProfile({
      commitmentSquares: [
        square({
          submitted: 35,
          missed: 1,
          points: 33,
          shade: "dark_green",
          breakdown: [
            { kind: "submitted", count: 35, points: 35 },
            { kind: "nmr", count: 1, points: -2 },
          ],
        }),
      ],
    });

    render(<PlayerProfileContent userId={1} />);
    await userEvent.click(
      screen.getByRole("button", {
        name: "Concert of Europe: Submitted 35 phases +35, Missed orders ×1 −2",
      })
    );

    const tooltip = within(await screen.findByRole("tooltip"));
    expect(tooltip.getByText("Submitted 35 phases")).toBeInTheDocument();
    expect(tooltip.getByText("Missed orders ×1")).toBeInTheDocument();
    expect(tooltip.getByText("Total")).toBeInTheDocument();
    expect(tooltip.getByText("+33")).toBeInTheDocument();
  });

  it("shows only the points of an anonymous game", async () => {
    profile = buildProfile({
      commitmentSquares: [
        square({
          anonymous: true,
          gameName: null,
          submitted: 5,
          points: 5,
          shade: "light_green",
          breakdown: [{ kind: "submitted", count: 5, points: 5 }],
        }),
      ],
    });

    render(<PlayerProfileContent userId={1} />);
    await userEvent.click(
      screen.getByRole("button", { name: "Anonymous game: +5" })
    );

    const tooltip = within(await screen.findByRole("tooltip"));
    expect(tooltip.getByText("Anonymous game")).toBeInTheDocument();
    expect(tooltip.queryByText("Submitted 5 phases")).not.toBeInTheDocument();
    expect(tooltip.queryByText("Total")).not.toBeInTheDocument();
  });
});
