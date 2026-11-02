import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter, Route, Routes, useLocation } from "react-router";
import { toast } from "sonner";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { ModerationReportOutput } from "@/api/generated/endpoints";
import { ModerationReport } from "./ModerationReport";

const retrieveReport = vi.fn();
const assignReport = vi.fn();
const unassignReport = vi.fn();
const approveReport = vi.fn();
const rejectReport = vi.fn();

vi.mock("@/api/generated/endpoints", async importOriginal => ({
  ...(await importOriginal<typeof import("@/api/generated/endpoints")>()),
  useModerationReportsRetrieveSuspense: (id: number) => ({
    data: retrieveReport(id),
  }),
  useModerationReportsAssignCreate: () => ({
    mutateAsync: assignReport,
    isPending: false,
  }),
  useModerationReportsUnassignCreate: () => ({
    mutateAsync: unassignReport,
    isPending: false,
  }),
  useModerationReportsApproveCreate: () => ({
    mutateAsync: approveReport,
    isPending: false,
  }),
  useModerationReportsRejectCreate: () => ({
    mutateAsync: rejectReport,
    isPending: false,
  }),
  useReportReasonsListSuspense: () => ({
    data: [{ key: "abuse_and_harassment", label: "Abuse and harassment", description: "" }],
  }),
}));

vi.mock("@/hooks/use-mobile", () => ({ useIsMobile: () => false }));

vi.mock("sonner", () => ({ toast: { success: vi.fn(), error: vi.fn() } }));

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
  review: null,
  assignedTo: null,
  actions: [],
  canViewGame: false,
  ...overrides,
});

const LocationProbe: React.FC = () => {
  const location = useLocation();
  return <p data-testid="location">{location.pathname + location.search}</p>;
};

const renderScreen = (
  initialEntries: React.ComponentProps<typeof MemoryRouter>["initialEntries"] = [
    { pathname: "/moderation/reports/5", state: { queueSearch: "?status=approved" } },
  ]
) =>
  render(
    <QueryClientProvider client={new QueryClient()}>
      <MemoryRouter initialEntries={initialEntries}>
        <Routes>
          <Route path="/moderation" element={<LocationProbe />} />
          <Route path="/game/:gameId" element={<LocationProbe />} />
          <Route path="/moderation/reports/:reportId" element={<ModerationReport />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  );

describe("ModerationReport", () => {
  beforeEach(() => {
    retrieveReport.mockReset();
    assignReport.mockReset();
    unassignReport.mockReset();
    approveReport.mockReset();
    rejectReport.mockReset();
    vi.mocked(toast.error).mockReset();
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

  it("omits the review while pending", () => {
    retrieveReport.mockReturnValue(report({}));
    renderScreen();

    expect(screen.getByText("Reporter's note")).toBeInTheDocument();
    expect(screen.queryByText(/ by$/)).not.toBeInTheDocument();
    expect(screen.queryByText("Moderator's note")).not.toBeInTheDocument();
  });

  it.each([
    ["approved", "Approved by"],
    ["rejected", "Rejected by"],
  ] as const)("shows who %s it", (status, label) => {
    retrieveReport.mockReturnValue(
      report({
        status,
        review: {
          reviewedBy: { userId: 7, name: "Mia Moderator" },
          note: "Checked the press history.",
          createdAt: "2026-10-02T12:00:00Z",
        },
      })
    );
    renderScreen();

    expect(screen.getByText(label)).toBeInTheDocument();
    expect(screen.getByText("Mia Moderator")).toBeInTheDocument();
    expect(screen.getByText("Moderator's note")).toBeInTheDocument();
    expect(screen.getByText("Checked the press history.")).toBeInTheDocument();
  });

  it("omits an empty moderator's note", () => {
    retrieveReport.mockReturnValue(
      report({
        status: "approved",
        review: {
          reviewedBy: { userId: 7, name: "Mia Moderator" },
          note: "",
          createdAt: "2026-10-02T12:00:00Z",
        },
      })
    );
    renderScreen();

    expect(screen.getByText("Approved by")).toBeInTheDocument();
    expect(screen.queryByText("Moderator's note")).not.toBeInTheDocument();
  });

  it("returns to the queue from the back button beside the title", async () => {
    retrieveReport.mockReturnValue(report({}));
    renderScreen();

    expect(screen.getByRole("heading", { name: "Report" })).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: "Back" }));

    expect(screen.getByTestId("location")).toHaveTextContent(
      "/moderation?status=approved"
    );
  });

  it("returns to the queue when opened directly", async () => {
    retrieveReport.mockReturnValue(report({}));
    renderScreen(["/moderation/reports/5"]);

    await userEvent.click(screen.getByRole("button", { name: "Back" }));

    expect(screen.getByTestId("location")).toHaveTextContent(/^\/moderation$/);
  });

  it("assigns a report nobody has taken", async () => {
    retrieveReport.mockReturnValue(
      report({
        actions: [
          { key: "assign", blockedReason: null },
          { key: "unassign", blockedReason: "not_assignee" },
        ],
      })
    );
    renderScreen();

    await userEvent.click(screen.getByRole("button", { name: "Assign to me" }));

    expect(assignReport).toHaveBeenCalledWith({ id: 5 });
    expect(screen.queryByRole("button", { name: "Unassign" })).not.toBeInTheDocument();
  });

  it("shows who has a report another moderator took", () => {
    retrieveReport.mockReturnValue(
      report({
        assignedTo: { userId: 200, name: "Sam Moderator" },
        actions: [
          { key: "assign", blockedReason: "already_assigned" },
          { key: "unassign", blockedReason: "not_assignee" },
        ],
      })
    );
    renderScreen();

    expect(screen.getByText("Assigned to Sam Moderator")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Assign to me" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Unassign" })).not.toBeInTheDocument();
  });

  it("lets the assigned moderator unassign themselves", async () => {
    retrieveReport.mockReturnValue(
      report({
        assignedTo: { userId: 300, name: "Mia Moderator" },
        actions: [
          { key: "assign", blockedReason: "already_assigned" },
          { key: "unassign", blockedReason: null },
        ],
      })
    );
    renderScreen();

    expect(screen.getByText("Assigned to you")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Unassign" }));

    expect(unassignReport).toHaveBeenCalledWith({ id: 5 });
  });

  it("explains a report from a game the moderator is in", () => {
    retrieveReport.mockReturnValue(
      report({
        actions: [
          { key: "assign", blockedReason: "game_member" },
          { key: "unassign", blockedReason: "not_assignee" },
        ],
      })
    );
    renderScreen();

    expect(screen.getByText("You're in this game")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Assign to me" })).not.toBeInTheDocument();
  });

  it("offers no assignment on a reviewed report", () => {
    retrieveReport.mockReturnValue(
      report({
        status: "approved",
        review: {
          reviewedBy: { userId: 7, name: "Mia Moderator" },
          note: "",
          createdAt: "2026-10-02T12:00:00Z",
        },
        actions: [
          { key: "assign", blockedReason: "already_reviewed" },
          { key: "unassign", blockedReason: "already_reviewed" },
        ],
      })
    );
    renderScreen();

    expect(screen.queryByRole("button", { name: "Assign to me" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Unassign" })).not.toBeInTheDocument();
  });

  it("shows an error when assigning fails", async () => {
    assignReport.mockRejectedValue(new Error("already_assigned"));
    retrieveReport.mockReturnValue(
      report({
        actions: [
          { key: "assign", blockedReason: null },
          { key: "unassign", blockedReason: "not_assignee" },
        ],
      })
    );
    renderScreen();

    await userEvent.click(screen.getByRole("button", { name: "Assign to me" }));

    expect(toast.error).toHaveBeenCalledWith("Failed to assign report");
  });

  it("opens the game for the assigned moderator", async () => {
    retrieveReport.mockReturnValue(
      report({
        assignedTo: { userId: 300, name: "Mia Moderator" },
        actions: [
          { key: "assign", blockedReason: "already_assigned" },
          { key: "unassign", blockedReason: null },
        ],
        canViewGame: true,
      })
    );
    renderScreen();

    await userEvent.click(screen.getByRole("link", { name: "View game" }));

    expect(screen.getByTestId("location")).toHaveTextContent(/^\/game\/g1$/);
  });

  it("hides the game from a moderator who cannot view it", () => {
    retrieveReport.mockReturnValue(
      report({
        assignedTo: { userId: 200, name: "Sam Moderator" },
        actions: [
          { key: "assign", blockedReason: "already_assigned" },
          { key: "unassign", blockedReason: "not_assignee" },
        ],
      })
    );
    renderScreen();

    expect(screen.queryByRole("link", { name: "View game" })).not.toBeInTheDocument();
  });

  describe("deciding", () => {
    const assigned = () =>
      report({
        assignedTo: { userId: 300, name: "Mia Moderator" },
        actions: [
          { key: "assign", blockedReason: "already_assigned" },
          { key: "unassign", blockedReason: null },
          { key: "approve", blockedReason: null },
          { key: "reject", blockedReason: null },
        ],
      });

    it("approves with a note after confirming", async () => {
      retrieveReport.mockReturnValue(assigned());
      renderScreen();

      await userEvent.type(
        screen.getByLabelText("Moderator's note"),
        "Slurs in global press."
      );
      await userEvent.click(screen.getByRole("button", { name: "Approve" }));

      expect(approveReport).not.toHaveBeenCalled();
      const dialog = await screen.findByRole("alertdialog");
      expect(
        within(dialog).getByText(
          "Decisions are final. Bruno Keller gets a mark for Abuse and harassment in this game."
        )
      ).toBeInTheDocument();

      await userEvent.click(within(dialog).getByRole("button", { name: "Approve" }));

      expect(approveReport).toHaveBeenCalledWith({
        id: 5,
        data: { note: "Slurs in global press." },
      });
      expect(rejectReport).not.toHaveBeenCalled();
    });

    it("rejects without a note after confirming", async () => {
      retrieveReport.mockReturnValue(assigned());
      renderScreen();

      await userEvent.click(screen.getByRole("button", { name: "Reject" }));
      const dialog = await screen.findByRole("alertdialog");
      expect(
        within(dialog).getByText(
          "Decisions are final. Nothing is added to Bruno Keller's profile."
        )
      ).toBeInTheDocument();

      await userEvent.click(within(dialog).getByRole("button", { name: "Reject" }));

      expect(rejectReport).toHaveBeenCalledWith({ id: 5, data: { note: "" } });
      expect(approveReport).not.toHaveBeenCalled();
    });

    it("saves nothing when the moderator cancels", async () => {
      retrieveReport.mockReturnValue(assigned());
      renderScreen();

      await userEvent.click(screen.getByRole("button", { name: "Approve" }));
      await userEvent.click(
        within(await screen.findByRole("alertdialog")).getByRole("button", {
          name: "Cancel",
        })
      );

      expect(approveReport).not.toHaveBeenCalled();
      expect(screen.queryByRole("alertdialog")).not.toBeInTheDocument();
    });

    it("shows an error when deciding fails", async () => {
      approveReport.mockRejectedValue(new Error("already_reviewed"));
      retrieveReport.mockReturnValue(assigned());
      renderScreen();

      await userEvent.click(screen.getByRole("button", { name: "Approve" }));
      await userEvent.click(
        within(await screen.findByRole("alertdialog")).getByRole("button", {
          name: "Approve",
        })
      );

      expect(toast.error).toHaveBeenCalledWith("Failed to approve report");
    });

    it("offers no decision to a moderator who isn't assigned", () => {
      retrieveReport.mockReturnValue(
        report({
          assignedTo: { userId: 200, name: "Sam Moderator" },
          actions: [
            { key: "assign", blockedReason: "already_assigned" },
            { key: "unassign", blockedReason: "not_assignee" },
            { key: "approve", blockedReason: "not_assignee" },
            { key: "reject", blockedReason: "not_assignee" },
          ],
        })
      );
      renderScreen();

      expect(screen.queryByLabelText("Moderator's note")).not.toBeInTheDocument();
      expect(screen.queryByRole("button", { name: "Approve" })).not.toBeInTheDocument();
      expect(screen.queryByRole("button", { name: "Reject" })).not.toBeInTheDocument();
    });

    it("shows who decided a report and when", () => {
      retrieveReport.mockReturnValue(
        report({
          status: "approved",
          review: {
            reviewedBy: { userId: 300, name: "Mia Moderator" },
            note: "",
            createdAt: "2026-10-02T12:00:00Z",
          },
          actions: [
            { key: "assign", blockedReason: "already_reviewed" },
            { key: "unassign", blockedReason: "already_reviewed" },
            { key: "approve", blockedReason: "already_reviewed" },
            { key: "reject", blockedReason: "already_reviewed" },
          ],
        })
      );
      renderScreen();

      expect(screen.getByText("Approved by")).toBeInTheDocument();
      expect(screen.getByText("Decided")).toBeInTheDocument();
      expect(screen.queryByRole("button", { name: "Approve" })).not.toBeInTheDocument();
    });
  });
});
