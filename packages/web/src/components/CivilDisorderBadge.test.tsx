import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";

import { CivilDisorderBadge } from "./CivilDisorderBadge";

describe("CivilDisorderBadge", () => {
  it("renders the civil disorder label", () => {
    render(<CivilDisorderBadge />);
    expect(screen.getByText("Civil Disorder")).toBeInTheDocument();
  });

  it("accepts an additional className", () => {
    const { container } = render(<CivilDisorderBadge className="custom-cls" />);
    expect(container.firstChild).toHaveClass("custom-cls");
  });
});
