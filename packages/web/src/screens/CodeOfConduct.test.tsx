import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { CodeOfConduct } from "./CodeOfConduct";

describe("CodeOfConduct", () => {
  it("renders the code of conduct", () => {
    render(<CodeOfConduct />);

    expect(
      screen.getByRole("heading", {
        level: 1,
        name: "Diplicity Code of Conduct",
      })
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Secret teaming" })
    ).toBeInTheDocument();
  });
});
