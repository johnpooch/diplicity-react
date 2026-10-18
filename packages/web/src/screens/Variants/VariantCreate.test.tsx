import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { VariantEdit } from "./index";
import { mockVariants } from "@/mocks/legacy";

const mockUpdate = vi.fn();

vi.mock("@/api/generated/endpoints", async importOriginal => {
  const actual = await importOriginal();
  return {
    ...(actual as Record<string, unknown>),
    useVariantsRetrieveSuspense: () => ({
      data: { ...mockVariants[0], id: "own-draft", canEdit: true, nations: [] },
    }),
    useVariantsUpdate: () => ({ mutateAsync: mockUpdate, isPending: false }),
    useVariantsNationsFlagUpdate: () => ({
      mutateAsync: vi.fn(),
      isPending: false,
    }),
    useVariantsNationsFlagDestroy: () => ({
      mutateAsync: vi.fn(),
      isPending: false,
    }),
  };
});

vi.mock("@/components/UserAvatar", () => ({
  UserAvatar: () => <div data-testid="user-avatar" />,
}));

const gamesWillBeDeleted = {
  response: {
    data: {
      confirm: [
        {
          code: "GAMES_WILL_BE_DELETED",
          message: "This update deletes 2 game(s) using this variant.",
          count: "2",
        },
      ],
    },
  },
};

const renderVariantEdit = () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <VariantEdit variantId="own-draft" />
      </MemoryRouter>
    </QueryClientProvider>
  );
};

const submitFiles = async () => {
  const user = userEvent.setup();
  await user.upload(
    await screen.findByLabelText("DVAR file (JSON)"),
    new File(["{}"], "variant.json", { type: "application/json" })
  );
  await user.upload(
    screen.getByLabelText("DSVG file (SVG)"),
    new File(["<svg/>"], "variant.svg", { type: "image/svg+xml" })
  );
  await user.click(screen.getByRole("button", { name: "Replace files" }));
  return user;
};

beforeEach(() => {
  mockUpdate.mockReset();
});

describe("VariantEdit", () => {
  it("updates without asking when no games would be deleted", async () => {
    mockUpdate.mockResolvedValue({});
    renderVariantEdit();

    await submitFiles();

    await waitFor(() => expect(mockUpdate).toHaveBeenCalledTimes(1));
    expect(mockUpdate.mock.calls[0][0].data.confirm).toBe(false);
    expect(screen.queryByRole("alertdialog")).not.toBeInTheDocument();
  });

  it("asks for confirmation before deleting games and resends with confirm", async () => {
    mockUpdate
      .mockRejectedValueOnce(gamesWillBeDeleted)
      .mockResolvedValueOnce({});
    renderVariantEdit();

    const user = await submitFiles();

    const dialog = await screen.findByRole("alertdialog");
    expect(dialog).toHaveTextContent(
      "2 games using this variant will be deleted"
    );

    await user.click(
      screen.getByRole("button", { name: "Delete games and update" })
    );

    await waitFor(() => expect(mockUpdate).toHaveBeenCalledTimes(2));
    expect(mockUpdate.mock.calls[1][0].data.confirm).toBe(true);
  });

  it("does not resend when the author cancels", async () => {
    mockUpdate.mockRejectedValueOnce(gamesWillBeDeleted);
    renderVariantEdit();

    const user = await submitFiles();

    await screen.findByRole("alertdialog");
    await user.click(screen.getByRole("button", { name: "Cancel" }));

    await waitFor(() =>
      expect(screen.queryByRole("alertdialog")).not.toBeInTheDocument()
    );
    expect(mockUpdate).toHaveBeenCalledTimes(1);
  });
});
