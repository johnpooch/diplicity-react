import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { DeleteGameAction } from "./DeleteGameAction";

const mockNavigate = vi.fn();
vi.mock("react-router", async importOriginal => {
  const actual = await importOriginal<typeof import("react-router")>();
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

const mockDeleteMutateAsync = vi.fn();

vi.mock("@/api/generated/endpoints", () => ({
  useGameDeleteDestroy: () => ({
    mutateAsync: mockDeleteMutateAsync,
    isPending: false,
  }),
  getGamesListQueryKey: () => ["games"],
}));

if (!Element.prototype.hasPointerCapture)
  Element.prototype.hasPointerCapture = () => false;
if (!Element.prototype.releasePointerCapture)
  Element.prototype.releasePointerCapture = () => {};
if (!Element.prototype.scrollIntoView)
  Element.prototype.scrollIntoView = () => {};

const renderAction = (sandbox: boolean) =>
  render(
    <QueryClientProvider client={new QueryClient()}>
      <MemoryRouter>
        <DeleteGameAction game={{ id: "game-1", sandbox }} />
      </MemoryRouter>
    </QueryClientProvider>
  );

describe("DeleteGameAction", () => {
  beforeEach(() => {
    mockNavigate.mockClear();
    mockDeleteMutateAsync.mockClear();
  });

  it("shows sandbox-specific copy in the confirmation dialog for a sandbox game", async () => {
    renderAction(true);

    await userEvent.click(screen.getByRole("button", { name: /delete game/i }));
    const dialog = within(screen.getByRole("alertdialog"));

    expect(dialog.getByText("Delete sandbox game")).toBeInTheDocument();
    expect(
      dialog.getByText(/permanently delete this sandbox game/i)
    ).toBeInTheDocument();
  });

  it("shows plain copy in the confirmation dialog for a non-sandbox game", async () => {
    renderAction(false);

    await userEvent.click(screen.getByRole("button", { name: /delete game/i }));
    const dialog = within(screen.getByRole("alertdialog"));

    expect(dialog.getByText("Delete game")).toBeInTheDocument();
    expect(
      dialog.getByText(/players who have joined will be notified/i)
    ).toBeInTheDocument();
  });

  it("deletes the game and navigates home on confirm", async () => {
    mockDeleteMutateAsync.mockResolvedValue({});
    renderAction(false);

    await userEvent.click(screen.getByRole("button", { name: /delete game/i }));
    await userEvent.click(screen.getByRole("button", { name: /^delete$/i }));

    expect(mockDeleteMutateAsync).toHaveBeenCalledWith({ gameId: "game-1" });
    expect(mockNavigate).toHaveBeenCalledWith("/");
  });
});
