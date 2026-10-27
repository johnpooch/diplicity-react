import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { describe, expect, it, vi } from "vitest";
import { Register } from "./Register";

vi.mock("@/api/generated/endpoints", async importOriginal => ({
  ...(await importOriginal<typeof import("@/api/generated/endpoints")>()),
  useAuthRegisterCreate: () => ({ mutateAsync: vi.fn(), isPending: false }),
}));

describe("Register", () => {
  it("links to the code of conduct", () => {
    render(
      <MemoryRouter>
        <Register />
      </MemoryRouter>
    );

    expect(
      screen.getByRole("link", { name: "Code of Conduct" })
    ).toHaveAttribute("href", "/code-of-conduct");
  });
});
