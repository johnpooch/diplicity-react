import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { NationBadge } from "./NationBadge";

const nations = [
  { name: "Russia", color: "#F5F5F5" },
  { name: "Germany", color: "#90A4AE" },
  { name: "Turkey", color: "#202020" },
];

describe("NationBadge", () => {
  it("renders nothing when nation is null", () => {
    const { container } = render(<NationBadge nations={nations} nation={null} />);
    expect(container).toBeEmptyDOMElement();
  });

  it("defaults the label to the nation name", () => {
    render(<NationBadge nations={nations} nation="Germany" />);
    expect(screen.getByText("Germany")).toBeInTheDocument();
  });

  it("renders custom children as the label", () => {
    render(
      <NationBadge nations={nations} nation="Germany">
        you
      </NationBadge>
    );
    expect(screen.getByText("you")).toBeInTheDocument();
  });

  it("uses dark text on a light nation colour", () => {
    render(<NationBadge nations={nations} nation="Russia" />);
    expect(screen.getByText("Russia")).toHaveStyle({ color: "#000000" });
  });

  it("uses light text on a dark nation colour", () => {
    render(<NationBadge nations={nations} nation="Turkey" />);
    expect(screen.getByText("Turkey")).toHaveStyle({ color: "#ffffff" });
  });
});
