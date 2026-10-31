import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AxiosError, AxiosHeaders } from "axios";
import { MemoryRouter, Route, Routes, useLocation } from "react-router";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { ModerationReportOutput } from "@/api/generated/endpoints";
import { ModerationQueue } from "./ModerationQueue";

const listReports = vi.fn();

vi.mock("@/api/generated/endpoints", async importOriginal => ({
  ...(await importOriginal<typeof import("@/api/generated/endpoints")>()),
  useModerationReportsListSuspense: (params: { status: string }) => ({
    data: listReports(params),
  }),
  useReportReasonsListSuspense: () => ({
    data: [
      { key: "abuse_and_harassment", label: "Abuse and harassment", description: "" },
      { key: "secret_teaming", label: "Secret teaming", description: "" },
    ],
  }),
}));

vi.mock("@/components/UserAvatar", () => ({ UserAvatar: () => null }));

const report = (overrides: Partial<ModerationReportOutput>): ModerationReportOutput => ({
  id: 1,
  reason: "abuse_and_harassment",
  note: "Slurs in press",
  status: "pending",
  createdAt: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(),
  gameId: "g1",
  gameName: "Spring Classic",
  variantName: "Classical",
  reporter: { id: 10, userId: 100, name: "Alice Moreau", nation: "England" },
  reported: { id: 11, userId: 101, name: "Bruno Keller", nation: "France" },
  ...overrides,
});

const notFound = () =>
  new AxiosError("Not Found", "ERR_BAD_REQUEST", undefined, undefined, {
    status: 404,
    statusText: "Not Found",
    data: {},
    headers: {},
    config: { headers: new AxiosHeaders() },
  });

const LocationProbe: React.FC = () => {
  const location = useLocation();
  return <p data-testid="location">{location.pathname + location.search}</p>;
};

const renderScreen = (path = "/moderation") =>
  render(
    <QueryClientProvider client={new QueryClient()}>
      <MemoryRouter initialEntries={[path]}>
        <Routes>
          <Route path="/moderation" element={<ModerationQueue />} />
          <Route path="/moderation/reports/:reportId" element={<p>Report page</p>} />
        </Routes>
        <LocationProbe />
      </MemoryRouter>
    </QueryClientProvider>
  );

describe("ModerationQueue", () => {
  beforeEach(() => {
    listReports.mockReset();
  });

  it("shows the pending tab by default", () => {
    listReports.mockReturnValue([report({})]);
    renderScreen();

    expect(listReports).toHaveBeenCalledWith({ status: "pending" });
    expect(screen.getByRole("tab", { name: "Pending" })).toHaveAttribute(
      "aria-selected",
      "true"
    );
  });

  it("shows reason, age, reporter, reported, game and variant on each row", () => {
    listReports.mockReturnValue([
      report({}),
      report({
        id: 2,
        reason: "secret_teaming",
        reporter: { id: 12, userId: null, name: null, nation: null },
      }),
    ]);
    renderScreen();

    const rows = within(screen.getByRole("list")).getAllByRole("link");
    expect(rows).toHaveLength(2);
    expect(within(rows[0]).getByText("Abuse and harassment")).toBeInTheDocument();
    expect(within(rows[0]).getByText("3 days ago")).toBeInTheDocument();
    expect(within(rows[0]).getByText("Alice Moreau (England)")).toBeInTheDocument();
    expect(within(rows[0]).getByText("Bruno Keller (France)")).toBeInTheDocument();
    expect(within(rows[0]).getByText("Spring Classic · Classical")).toBeInTheDocument();
    expect(rows[0]).toHaveAttribute("href", "/moderation/reports/1");
    expect(within(rows[1]).getByText("Secret teaming")).toBeInTheDocument();
    expect(within(rows[1]).getByText("Deleted account")).toBeInTheDocument();
  });

  it("switches status through the URL", async () => {
    listReports.mockReturnValue([]);
    renderScreen();

    await userEvent.click(screen.getByRole("tab", { name: "Rejected" }));

    expect(screen.getByTestId("location")).toHaveTextContent(
      "/moderation?status=rejected"
    );
    expect(listReports).toHaveBeenLastCalledWith({ status: "rejected" });
    expect(screen.getByText("No rejected reports")).toBeInTheDocument();
  });

  it("reads the tab from the URL", () => {
    listReports.mockReturnValue([report({ status: "approved" })]);
    renderScreen("/moderation?status=approved");

    expect(listReports).toHaveBeenCalledWith({ status: "approved" });
    expect(screen.getByRole("tab", { name: "Approved" })).toHaveAttribute(
      "aria-selected",
      "true"
    );
  });

  it("falls back to pending for an unknown status", () => {
    listReports.mockReturnValue([]);
    renderScreen("/moderation?status=under_review");

    expect(listReports).toHaveBeenCalledWith({ status: "pending" });
    expect(screen.getByText("No pending reports")).toBeInTheDocument();
  });

  it("opens a report from its row", async () => {
    listReports.mockReturnValue([report({ id: 7 })]);
    renderScreen();

    await userEvent.click(within(screen.getByRole("list")).getByRole("link"));

    expect(screen.getByText("Report page")).toBeInTheDocument();
  });

  it("renders the not-found notice when the API answers 404", () => {
    vi.spyOn(console, "error").mockImplementation(() => {});
    listReports.mockImplementation(() => {
      throw notFound();
    });
    renderScreen();

    expect(screen.getByText("This game is no longer available")).toBeInTheDocument();
    expect(screen.queryByRole("tab")).not.toBeInTheDocument();
  });
});
