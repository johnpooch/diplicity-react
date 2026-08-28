import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";

import { KickedBadge } from "./KickedBadge";

describe("KickedBadge", () => {
  it("renders the removed label", () => {
    render(<KickedBadge />);
    expect(screen.getByText("Removed")).toBeInTheDocument();
  });

  it("accepts an additional className", () => {
    const { container } = render(<KickedBadge className="custom-cls" />);
    expect(container.firstChild).toHaveClass("custom-cls");
  });
});
