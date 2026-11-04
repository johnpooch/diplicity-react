import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { describe, expect, it } from "vitest";
import { HowRatingsWork } from "./HowRatingsWork";

describe("HowRatingsWork", () => {
  it("explains each point", () => {
    render(
      <MemoryRouter>
        <HowRatingsWork />
      </MemoryRouter>
    );
    expect(screen.getByText("What your rating shows")).toBeInTheDocument();
    expect(screen.getByText("How a game counts")).toBeInTheDocument();
    expect(screen.getByText("New ratings")).toBeInTheDocument();
    expect(screen.getByText("Leaving and taking over")).toBeInTheDocument();
    expect(screen.getByText("Which games are ranked")).toBeInTheDocument();
  });
});
