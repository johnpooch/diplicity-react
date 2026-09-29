import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import {
  createLoadingSpinnerElement,
  LoadingSpinner,
} from "./loading-spinner";

describe("LoadingSpinner", () => {
  it("announces its loading state by default", () => {
    render(<LoadingSpinner />);

    expect(screen.getByRole("status", { name: "Loading" })).toHaveClass(
      "animate-spin",
      "size-6"
    );
  });

  it("can be decorative and use another size", () => {
    const { container } = render(<LoadingSpinner label={null} size="sm" />);
    const spinner = container.querySelector('[data-slot="loading-spinner"]');

    expect(spinner).toHaveAttribute("aria-hidden", "true");
    expect(spinner).not.toHaveAttribute("role");
    expect(spinner).toHaveClass("animate-spin", "size-4");
  });

  it("creates the same spinner for imperative integrations", () => {
    const host = createLoadingSpinnerElement({ size: "lg" });
    const spinner = host.querySelector("svg");

    expect(spinner).toHaveAttribute("aria-hidden", "true");
    expect(spinner).toHaveClass(
      "lucide-loader-circle",
      "loading-spinner",
      "animate-spin",
      "size-10"
    );
    expect(spinner?.querySelector("path")).toHaveAttribute(
      "d",
      "M21 12a9 9 0 1 1-6.219-8.56"
    );
    expect((spinner as SVGSVGElement).dataset.slot).toBe("loading-spinner");
  });
});
