import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";

import { WithdrawnBadge } from "./WithdrawnBadge";

describe("WithdrawnBadge", () => {
  it("renders the withdrawn label", () => {
    render(<WithdrawnBadge />);
    expect(screen.getByText("Withdrawn")).toBeInTheDocument();
  });

  it("accepts an additional className", () => {
    const { container } = render(<WithdrawnBadge className="custom-cls" />);
    expect(container.firstChild).toHaveClass("custom-cls");
  });
});
