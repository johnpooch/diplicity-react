import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";

import { EliminatedBadge } from "./EliminatedBadge";

describe("EliminatedBadge", () => {
  it("renders the eliminated label", () => {
    render(<EliminatedBadge />);
    expect(screen.getByText("Eliminated")).toBeInTheDocument();
  });

  it("accepts an additional className", () => {
    const { container } = render(<EliminatedBadge className="custom-cls" />);
    expect(container.firstChild).toHaveClass("custom-cls");
  });
});
