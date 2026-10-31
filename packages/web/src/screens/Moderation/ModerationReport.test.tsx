import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter, Route, Routes } from "react-router";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { ModerationReportOutput } from "@/api/generated/endpoints";
import { ModerationReport } from "./ModerationReport";

const retrieveReport = vi.fn();

vi.mock("@/api/generated/endpoints", async importOriginal => ({
  ...(await importOriginal<typeof import("@/api/generated/endpoints")>()),
  useModerationReportsRetrieveSuspense: (id: number) => ({
    data: retrieveReport(id),
  }),
  useReportReasonsListSuspense: () => ({
    data: [{ key: "abuse_and_harassment", label: "Abuse and harassment", description: "" }],
  }),
}));

vi.mock("@/hooks/use-mobile", () => ({ useIsMobile: () => false }));

const report = (overrides: Partial<ModerationReportOutput>): ModerationReportOutput => ({
  id: 5,
  reason: "abuse_and_harassment",
  note: "Slurs in press",
  status: "pending",
  createdAt: "2026-10-28T12:00:00Z",
  gameId: "g1",
  gameName: "Spring Classic",
  variantName: "Classical",
  reporter: { id: 10, userId: 100, name: "Alice Moreau", nation: "England" },
  reported: { id: 11, userId: 101, name: "Bruno Keller", nation: "France" },
  reviewedBy: null,
  ...overrides,
});

const renderScreen = () =>
  render(
    <QueryClientProvider client={new QueryClient()}>
      <MemoryRouter
        initialEntries={["/moderation?status=approved", "/moderation/reports/5"]}
        initialIndex={1}
      >
        <Routes>
          <Route path="/moderation" element={<p>Moderation queue</p>} />
          <Route path="/moderation/reports/:reportId" element={<ModerationReport />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  );

describe("ModerationReport", () => {
  beforeEach(() => {
    retrieveReport.mockReset();
  });

  it("shows the report", () => {
    retrieveReport.mockReturnValue(report({}));
    renderScreen();

    expect(retrieveReport).toHaveBeenCalledWith(5);
    expect(screen.getByText("Abuse and harassment")).toBeInTheDocument();
    expect(screen.getByText("Pending")).toBeInTheDocument();
    expect(screen.getByText("Spring Classic · Classical")).toBeInTheDocument();
    expect(screen.getByText("Alice Moreau (England)")).toBeInTheDocument();
    expect(screen.getByText("Bruno Keller (France)")).toBeInTheDocument();
    expect(screen.getByText("Slurs in press")).toBeInTheDocument();
  });

  it("omits the reviewer while pending", () => {
    retrieveReport.mockReturnValue(report({}));
    renderScreen();

    expect(screen.queryByText(/ by$/)).not.toBeInTheDocument();
  });

  it.each([
    ["approved", "Approved by"],
    ["rejected", "Rejected by"],
  ] as const)("shows who %s it", (status, label) => {
    retrieveReport.mockReturnValue(
      report({ status, reviewedBy: { userId: 7, name: "Mia Moderator" } })
    );
    renderScreen();

    expect(screen.getByText(label)).toBeInTheDocument();
    expect(screen.getByText("Mia Moderator")).toBeInTheDocument();
  });

  it("returns to the queue from the back button beside the title", async () => {
    retrieveReport.mockReturnValue(report({}));
    renderScreen();

    expect(screen.getByRole("heading", { name: "Report" })).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: "Back" }));

    expect(screen.getByText("Moderation queue")).toBeInTheDocument();
  });
});
