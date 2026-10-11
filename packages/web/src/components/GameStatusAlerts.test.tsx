import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";

import { GameStatusAlerts } from "./GameStatusAlerts";

describe("GameStatusAlerts", () => {
  it("counts only playable nations towards the players needed to start", () => {
    render(
      <GameStatusAlerts
        game={{ status: "pending" }}
        variant={{
          nations: [
            { nonPlayable: false },
            { nonPlayable: false },
            { nonPlayable: true },
          ],
        }}
      />
    );
    expect(
      screen.getByText(/The game will start once 2 players have joined/)
    ).toBeInTheDocument();
  });
});
