import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { Variant, VariantNation } from "@/api/generated/endpoints";
import { TooltipProvider } from "@/components/ui/tooltip";
import { VariantDetailsScreen } from "./VariantDetailsScreen";

let variant: Variant;

vi.mock("@/api/generated/endpoints", async importOriginal => ({
  ...(await importOriginal<typeof import("@/api/generated/endpoints")>()),
  useGameRetrieveSuspense: () => ({ data: { variantId: "classical" } }),
}));

vi.mock("@/hooks/useGameVariant", () => ({
  useGameVariant: () => variant,
}));

vi.mock("@/hooks/use-mobile", () => ({ useIsMobile: () => false }));

vi.mock("@/components/MapView", () => ({ MapView: () => null }));

const buildNation = (
  overrides: Partial<VariantNation> = {}
): VariantNation => ({
  nationId: "england",
  name: "England",
  color: "#000000",
  nonPlayable: false,
  flagUrl: null,
  soloVictorySupplyCenters: null,
  handicap: null,
  ...overrides,
});

const buildVariant = (nations: VariantNation[]): Variant => ({
  id: "classical",
  name: "Classical",
  description: "",
  rules: "",
  unitScaling: 1,
  status: "published",
  official: true,
  ownerId: null,
  ownerUsername: null,
  canEdit: false,
  ranked: true,
  victoryConditions: {
    soloVictorySupplyCenters: 18,
    gameEndsYear: null,
    drawAfterYear: null,
  },
  svgUrl: null,
  nations,
  provinces: [],
  templatePhase: { year: 1901, units: [], supplyCenters: [] },
});

const renderScreen = () =>
  render(
    <TooltipProvider>
      <MemoryRouter initialEntries={["/game/g1/phase/1/game-info/variant"]}>
        <Routes>
          <Route
            path="/game/:gameId/phase/:phaseId/game-info/variant"
            element={<VariantDetailsScreen />}
          />
        </Routes>
      </MemoryRouter>
    </TooltipProvider>
  );

const rowValue = (label: string) =>
  screen.getByText(label, { selector: "span" }).nextElementSibling?.textContent;

describe("VariantDetailsScreen", () => {
  beforeEach(() => {
    variant = buildVariant([]);
  });

  it("lists each nation's handicap with its sign", () => {
    variant = buildVariant([
      buildNation({ nationId: "france", name: "France", handicap: 25 }),
      buildNation({ nationId: "austria", name: "Austria", handicap: -30 }),
      buildNation({ nationId: "germany", name: "Germany", handicap: 0 }),
    ]);

    renderScreen();

    expect(screen.getByText("Ranked Handicaps")).toBeInTheDocument();
    expect(rowValue("France")).toBe("+25");
    expect(rowValue("Austria")).toBe("-30");
    expect(rowValue("Germany")).toBe("0");
  });

  it("orders nations from highest to lowest handicap", () => {
    variant = buildVariant([
      buildNation({ nationId: "austria", name: "Austria", handicap: -30 }),
      buildNation({ nationId: "france", name: "France", handicap: 25 }),
      buildNation({ nationId: "germany", name: "Germany", handicap: 0 }),
    ]);

    renderScreen();

    const labels = ["France", "Germany", "Austria"].map(name =>
      screen.getByText(name, { selector: "span" })
    );
    expect(
      labels[0].compareDocumentPosition(labels[1]) &
        Node.DOCUMENT_POSITION_FOLLOWING
    ).toBeTruthy();
    expect(
      labels[1].compareDocumentPosition(labels[2]) &
        Node.DOCUMENT_POSITION_FOLLOWING
    ).toBeTruthy();
  });

  it("explains what the handicaps are for", () => {
    variant = buildVariant([buildNation({ handicap: 15 })]);

    renderScreen();

    expect(
      screen.getByRole("button", { name: "What are Ranked Handicaps?" })
    ).toBeInTheDocument();
  });

  it("omits nations without a handicap", () => {
    variant = buildVariant([
      buildNation({ nationId: "france", name: "France", handicap: 25 }),
      buildNation({ nationId: "neutral", name: "Neutral", nonPlayable: true }),
    ]);

    renderScreen();

    expect(screen.queryByText("Neutral", { selector: "span" })).toBeNull();
  });

  it("hides the section when the variant has no handicaps", () => {
    variant = buildVariant([buildNation()]);

    renderScreen();

    expect(screen.queryByText("Ranked Handicaps")).toBeNull();
  });
});
