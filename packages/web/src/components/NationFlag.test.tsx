import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { NationFlag } from "./NationFlag";

describe("NationFlag", () => {
  it("uses a 2px nation-colour ring for compact flags", () => {
    render(
      <NationFlag
        flagUrl="/england.svg"
        alt="England"
        size="sm"
        color="#123456"
      />
    );

    expect(screen.getByRole("img", { name: "England" })).toHaveStyle({
      boxShadow: "0 0 0 2px #123456",
    });
  });

  it("uses a 3px nation-colour ring for large flags", () => {
    render(
      <NationFlag
        flagUrl="/france.svg"
        alt="France"
        size="lg"
        color="#654321"
      />
    );

    expect(screen.getByRole("img", { name: "France" })).toHaveStyle({
      boxShadow: "0 0 0 3px #654321",
    });
  });

  it("allows compact contexts to override a large flag's ring width", () => {
    render(
      <NationFlag
        flagUrl="/france.svg"
        alt="France in chat"
        size="lg"
        color="#654321"
        ringWidth={2}
      />
    );

    expect(screen.getByRole("img", { name: "France in chat" })).toHaveStyle({
      boxShadow: "0 0 0 2px #654321",
    });
  });
});
