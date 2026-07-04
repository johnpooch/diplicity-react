import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { VariantsList } from "./index";
import { mockVariants } from "@/mocks/legacy";

const mockUseVariantsListSuspense = vi.fn();
const mockUseVariantsMineListSuspense = vi.fn();

vi.mock("@/api/generated/endpoints", async importOriginal => {
  const actual = await importOriginal();
  return {
    ...(actual as Record<string, unknown>),
    useVariantsListSuspense: () => mockUseVariantsListSuspense(),
    useVariantsMineListSuspense: () => mockUseVariantsMineListSuspense(),
    useVariantsDestroy: () => ({ mutateAsync: vi.fn(), isPending: false }),
    useSandboxGameCreate: () => ({ mutateAsync: vi.fn(), isPending: false }),
  };
});

vi.mock("@/components/MapView", () => ({
  MapView: () => <div data-testid="map-preview" />,
}));

const publishedVariant = {
  ...mockVariants[0],
  id: "classical",
  name: "Classical",
  status: "published",
  canEdit: false,
};

const ownDraft = {
  ...mockVariants[0],
  id: "own-draft",
  name: "Own Draft",
  status: "draft",
  canEdit: true,
};

const renderVariantsList = () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <VariantsList />
      </MemoryRouter>
    </QueryClientProvider>
  );
};

beforeEach(() => {
  mockUseVariantsListSuspense.mockReset();
  mockUseVariantsListSuspense.mockReturnValue({ data: [publishedVariant] });
  mockUseVariantsMineListSuspense.mockReset();
  mockUseVariantsMineListSuspense.mockReturnValue({ data: [ownDraft] });
});

describe("VariantsList", () => {
  it("shows both the published catalogue and the user's own drafts", async () => {
    renderVariantsList();

    expect(await screen.findByText("Classical")).toBeInTheDocument();
    expect(screen.getByText("Own Draft")).toBeInTheDocument();
  });

  it("lists drafts before published variants", async () => {
    renderVariantsList();

    const headings = await screen.findAllByRole("heading", { level: 3 });
    expect(headings.map(h => h.textContent)).toEqual(["Own Draft", "Classical"]);
  });

  it("shows the empty state when there are no variants", async () => {
    mockUseVariantsListSuspense.mockReturnValue({ data: [] });
    mockUseVariantsMineListSuspense.mockReturnValue({ data: [] });

    renderVariantsList();

    expect(await screen.findByText("No variants yet")).toBeInTheDocument();
  });
});
