import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AxiosError, AxiosHeaders } from "axios";
import { MemoryRouter, Route, Routes, useLocation } from "react-router";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { ModerationReportOutput } from "@/api/generated/endpoints";
import { ModerationQueue } from "./ModerationQueue";

const listReports = vi.fn();
const isMobile = vi.fn();

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

vi.mock("@/hooks/use-mobile", () => ({ useIsMobile: () => isMobile() }));

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
  review: null,
  assignedTo: null,
  actions: [
    { key: "assign", blockedReason: null },
    { key: "unassign", blockedReason: "not_assignee" },
  ],
  canViewGame: false,
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

const ReportPageProbe: React.FC = () => {
  const { state } = useLocation();
  return <p>Report page {state?.queueSearch}</p>;
};

const renderScreen = (path = "/moderation") =>
  render(
    <QueryClientProvider client={new QueryClient()}>
      <MemoryRouter initialEntries={[path]}>
        <Routes>
          <Route path="/moderation" element={<ModerationQueue />} />
          <Route path="/moderation/reports/:reportId" element={<ReportPageProbe />} />
        </Routes>
        <LocationProbe />
      </MemoryRouter>
    </QueryClientProvider>
  );

const filterButton = (selected: string) =>
  screen.getByRole("button", {
    name: `Choose report status, ${selected} selected`,
  });

describe("ModerationQueue", () => {
  beforeEach(() => {
    listReports.mockReset();
    isMobile.mockReturnValue(false);
  });

  it("shows pending reports by default", () => {
    listReports.mockReturnValue([report({})]);
    renderScreen();

    expect(listReports).toHaveBeenCalledWith({ status: "pending" });
    expect(filterButton("Pending")).toHaveTextContent("Pending");
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

  it("offers pending, approved and rejected from a menu on desktop", async () => {
    listReports.mockReturnValue([]);
    renderScreen();

    await userEvent.click(filterButton("Pending"));
    expect(screen.getByRole("button", { name: "Pending" })).toHaveAttribute(
      "aria-pressed",
      "true"
    );
    expect(screen.getByRole("button", { name: "Approved" })).toHaveAttribute(
      "aria-pressed",
      "false"
    );

    await userEvent.click(screen.getByRole("button", { name: "Rejected" }));

    expect(screen.getByTestId("location")).toHaveTextContent(
      "/moderation?status=rejected"
    );
    expect(listReports).toHaveBeenLastCalledWith({ status: "rejected" });
    expect(screen.getByText("No rejected reports")).toBeInTheDocument();
    expect(filterButton("Rejected")).toBeInTheDocument();
  });

  it("opens the filter as a bottom sheet on mobile", async () => {
    isMobile.mockReturnValue(true);
    listReports.mockReturnValue([]);
    renderScreen();

    await userEvent.click(filterButton("Pending"));
    const sheet = screen.getByRole("dialog");
    await userEvent.click(within(sheet).getByRole("button", { name: "Approved" }));

    expect(screen.getByTestId("location")).toHaveTextContent(
      "/moderation?status=approved"
    );
    expect(listReports).toHaveBeenLastCalledWith({ status: "approved" });
  });

  it("returns to pending without a status in the URL", async () => {
    listReports.mockReturnValue([]);
    renderScreen("/moderation?status=approved");

    await userEvent.click(filterButton("Approved"));
    await userEvent.click(screen.getByRole("button", { name: "Pending" }));

    expect(screen.getByTestId("location")).toHaveTextContent(/^\/moderation$/);
    expect(listReports).toHaveBeenLastCalledWith({ status: "pending" });
  });

  it("reads the status from the URL", () => {
    listReports.mockReturnValue([report({ status: "approved" })]);
    renderScreen("/moderation?status=approved");

    expect(listReports).toHaveBeenCalledWith({ status: "approved" });
    expect(filterButton("Approved")).toBeInTheDocument();
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

  it("passes the queue filter to the report page", async () => {
    listReports.mockReturnValue([report({ status: "approved" })]);
    renderScreen("/moderation?status=approved");

    await userEvent.click(within(screen.getByRole("list")).getByRole("link"));

    expect(screen.getByText("Report page ?status=approved")).toBeInTheDocument();
  });

  it("renders the not-found notice when the API answers 404", () => {
    vi.spyOn(console, "error").mockImplementation(() => {});
    listReports.mockImplementation(() => {
      throw notFound();
    });
    renderScreen();

    expect(screen.getByText("This game is no longer available")).toBeInTheDocument();
    expect(screen.queryByRole("list")).not.toBeInTheDocument();
  });

  it("says nothing about assignment on a free report", () => {
    listReports.mockReturnValue([report({})]);
    renderScreen();

    expect(screen.queryByText(/Assigned to/)).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Assign to me" })).not.toBeInTheDocument();
  });

  it("shows who has a report another moderator took", () => {
    listReports.mockReturnValue([
      report({
        assignedTo: { userId: 200, name: "Sam Moderator" },
        actions: [
          { key: "assign", blockedReason: "already_assigned" },
          { key: "unassign", blockedReason: "not_assignee" },
        ],
      }),
    ]);
    renderScreen();

    const row = within(screen.getByRole("list")).getByRole("link");
    expect(within(row).getByText("Assigned to Sam Moderator")).toBeInTheDocument();
  });

  it("shows a report the moderator took as theirs", () => {
    listReports.mockReturnValue([
      report({
        assignedTo: { userId: 300, name: "Mia Moderator" },
        actions: [
          { key: "assign", blockedReason: "already_assigned" },
          { key: "unassign", blockedReason: null },
        ],
      }),
    ]);
    renderScreen();

    expect(screen.getByText("Assigned to you")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Unassign" })).not.toBeInTheDocument();
  });

  it("explains a report from a game the moderator is in", () => {
    listReports.mockReturnValue([
      report({
        actions: [
          { key: "assign", blockedReason: "game_member" },
          { key: "unassign", blockedReason: "not_assignee" },
        ],
      }),
    ]);
    renderScreen();

    expect(screen.getByText("You're in this game")).toBeInTheDocument();
  });

  it("says nothing about assignment on a reviewed report", () => {
    listReports.mockReturnValue([
      report({
        status: "approved",
        assignedTo: { userId: 200, name: "Sam Moderator" },
        actions: [
          { key: "assign", blockedReason: "already_reviewed" },
          { key: "unassign", blockedReason: "already_reviewed" },
        ],
      }),
    ]);
    renderScreen("/moderation?status=approved");

    expect(screen.queryByText(/Assigned to/)).not.toBeInTheDocument();
  });
});
