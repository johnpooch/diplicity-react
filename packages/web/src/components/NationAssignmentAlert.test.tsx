import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router";
import { describe, it, expect, vi } from "vitest";

import { NationAssignmentAlert } from "./NationAssignmentAlert";

const mockNavigate = vi.fn();

vi.mock("react-router", async importOriginal => {
  const actual = await importOriginal<typeof import("react-router")>();
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

describe("NationAssignmentAlert", () => {
  it("navigates to nation assignment", async () => {
    const user = userEvent.setup();
    render(
      <MemoryRouter>
        <NationAssignmentAlert gameId="game-1" />
      </MemoryRouter>
    );

    await user.click(screen.getByRole("button", { name: /assign nations/i }));

    expect(mockNavigate).toHaveBeenCalledWith("/nation-assignment/game-1");
  });
});
