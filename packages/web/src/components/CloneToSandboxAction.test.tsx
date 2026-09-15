import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { CloneToSandboxAction } from "./CloneToSandboxAction";

const mockNavigate = vi.fn();
vi.mock("react-router", async importOriginal => {
  const actual = await importOriginal<typeof import("react-router")>();
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

const mockCloneMutateAsync = vi.fn();

vi.mock("@/api/generated/endpoints", () => ({
  useGameCloneToSandboxCreate: () => ({
    mutateAsync: mockCloneMutateAsync,
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

const renderAction = () =>
  render(
    <QueryClientProvider client={new QueryClient()}>
      <MemoryRouter>
        <CloneToSandboxAction game={{ id: "game-1" }} />
      </MemoryRouter>
    </QueryClientProvider>
  );

describe("CloneToSandboxAction", () => {
  beforeEach(() => {
    mockNavigate.mockClear();
    mockCloneMutateAsync.mockClear();
  });

  it("shows a confirmation dialog before cloning", async () => {
    renderAction();

    await userEvent.click(
      screen.getByRole("button", { name: /clone to sandbox/i })
    );

    expect(
      screen.getByText(/a sandbox copy of this game will be created/i)
    ).toBeInTheDocument();
  });

  it("clones the game and navigates to the new sandbox on confirm", async () => {
    mockCloneMutateAsync.mockResolvedValue({ id: "sandbox-2" });
    renderAction();

    await userEvent.click(
      screen.getByRole("button", { name: /clone to sandbox/i })
    );
    await userEvent.click(
      screen.getByRole("button", { name: /create sandbox/i })
    );

    expect(mockCloneMutateAsync).toHaveBeenCalledWith({
      gameId: "game-1",
      data: {},
    });
    expect(mockNavigate).toHaveBeenCalledWith("/game/sandbox-2");
  });
});
