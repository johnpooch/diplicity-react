import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Link, MemoryRouter } from "react-router";
import { describe, expect, it, vi } from "vitest";
import { RowActionButton, SecondaryButton } from "./role-buttons";

describe("RowActionButton", () => {
  it("does not submit an enclosing form", async () => {
    const onSubmit = vi.fn(event => event.preventDefault());
    render(
      <form onSubmit={onSubmit}>
        <RowActionButton>Mute notifications</RowActionButton>
      </form>
    );

    await userEvent.click(
      screen.getByRole("button", { name: "Mute notifications" })
    );

    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("renders its child link when asChild is set", () => {
    render(
      <MemoryRouter>
        <RowActionButton asChild>
          <Link to="/player/1">View my profile</Link>
        </RowActionButton>
      </MemoryRouter>
    );

    const link = screen.getByRole("link", { name: "View my profile" });
    expect(link).toHaveAttribute("href", "/player/1");
    expect(link).not.toHaveAttribute("type");
  });

  it("marks a destructive row", () => {
    render(<RowActionButton destructive>Leave game</RowActionButton>);

    expect(screen.getByRole("button", { name: "Leave game" })).toHaveClass(
      "text-destructive"
    );
  });
});

describe("SecondaryButton", () => {
  it("marks a destructive action", () => {
    render(<SecondaryButton destructive>Delete account</SecondaryButton>);

    expect(screen.getByRole("button", { name: "Delete account" })).toHaveClass(
      "text-destructive"
    );
  });
});
