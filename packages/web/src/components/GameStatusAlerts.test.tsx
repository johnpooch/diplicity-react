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

  it("tells a remaining player which nations are in civil disorder", () => {
    render(
      <GameStatusAlerts
        game={{
          status: "active",
          canWithdraw: true,
          members: [
            { nation: "England", civilDisorder: false, replaceable: false },
            { nation: "France", civilDisorder: true, replaceable: true },
            { nation: "Italy", civilDisorder: true, replaceable: true },
          ],
        }}
      />
    );
    expect(
      screen.getByText(/France and Italy are in civil disorder/)
    ).toBeInTheDocument();
    expect(
      screen.getByText(/find a replacement player, propose a draw, or withdraw/)
    ).toBeInTheDocument();
  });

  it("ignores a civil disorder seat that has been replaced", () => {
    render(
      <GameStatusAlerts
        game={{
          status: "active",
          canWithdraw: true,
          members: [
            { nation: "France", civilDisorder: true, replaceable: false },
            { nation: "France", civilDisorder: false, replaceable: false },
          ],
        }}
      />
    );
    expect(screen.queryByText(/civil disorder/)).not.toBeInTheDocument();
  });

  it("does not alert a player who is no longer playing", () => {
    render(
      <GameStatusAlerts
        game={{
          status: "active",
          canWithdraw: false,
          members: [
            { nation: "England", civilDisorder: true, replaceable: true },
            { nation: "France", civilDisorder: true, replaceable: true },
          ],
        }}
      />
    );
    expect(screen.queryByText(/civil disorder/)).not.toBeInTheDocument();
  });
});
