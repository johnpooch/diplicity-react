import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect } from "vitest";

import { CommitmentBadge } from "./CommitmentBadge";

describe("CommitmentBadge", () => {
  it.each([
    ["high", "High"],
    ["medium", "Medium"],
    ["low", "Low"],
    ["undefined", "New"],
  ])("renders the %s tier as %s", (commitment, label) => {
    render(<CommitmentBadge commitment={commitment} />);
    expect(screen.getByText(label)).toBeInTheDocument();
  });

  it("renders nothing for an unknown tier", () => {
    const { container } = render(<CommitmentBadge commitment="bogus" />);
    expect(container).toBeEmptyDOMElement();
  });

  it("shows an explanation when tapped", async () => {
    const user = userEvent.setup();
    render(<CommitmentBadge commitment="low" />);

    await user.click(screen.getByRole("button", { name: "Commitment: Low" }));

    expect(
      screen.getByText(/missed many order deadlines/i)
    ).toBeInTheDocument();
  });
});
