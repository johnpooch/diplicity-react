import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AxiosError, AxiosHeaders } from "axios";
import { MemoryRouter, Route, Routes } from "react-router";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ReportMemberScreen } from "./ReportMemberScreen";

const mutateAsync = vi.fn();

vi.mock("@/api/generated/endpoints", async importOriginal => ({
  ...(await importOriginal<typeof import("@/api/generated/endpoints")>()),
  useReportReasonsListSuspense: () => ({
    data: [
      {
        key: "abuse_and_harassment",
        label: "Abuse and harassment",
        description: "This player insulted or demeaned other players.",
      },
      {
        key: "other",
        label: "Other",
        description: "Explain what happened in the note.",
      },
    ],
  }),
  useGameMemberReportCreate: () => ({ mutateAsync, isPending: false }),
}));

vi.mock("@/hooks/use-mobile", () => ({ useIsMobile: () => false }));

const forbidden = (code: string) =>
  new AxiosError("Forbidden", "403", undefined, undefined, {
    status: 403,
    statusText: "Forbidden",
    headers: {},
    config: { headers: new AxiosHeaders() },
    data: { code },
  });

const renderScreen = () =>
  render(
    <QueryClientProvider client={new QueryClient()}>
      <MemoryRouter initialEntries={["/game/g1/phase/7/member/3/report"]}>
        <Routes>
          <Route
            path="/game/:gameId/phase/:phaseId/member/:memberId/report"
            element={<ReportMemberScreen />}
          />
          <Route
            path="/game/:gameId/phase/:phaseId/member/:memberId"
            element={<p>Player details</p>}
          />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  );

describe("ReportMemberScreen", () => {
  beforeEach(() => {
    mutateAsync.mockReset();
  });

  it("shows each reason with its description", () => {
    renderScreen();

    expect(screen.getByRole("radio", { name: /Abuse and harassment/ })).toBeInTheDocument();
    expect(
      screen.getByText("This player insulted or demeaned other players.")
    ).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Code of Conduct" })).toHaveAttribute(
      "href",
      "/code-of-conduct"
    );
  });

  it("submits the reason and note, then returns to player details", async () => {
    mutateAsync.mockResolvedValue({});
    renderScreen();

    await userEvent.click(screen.getByRole("radio", { name: /Abuse and harassment/ }));
    await userEvent.type(screen.getByRole("textbox", { name: "Note" }), "Slurs in press");
    await userEvent.click(screen.getByRole("button", { name: "Submit report" }));

    await waitFor(() =>
      expect(mutateAsync).toHaveBeenCalledWith({
        gameId: "g1",
        memberId: 3,
        data: { reason: "abuse_and_harassment", note: "Slurs in press" },
      })
    );
    expect(await screen.findByText("Player details")).toBeInTheDocument();
  });

  it("does not submit without a reason", async () => {
    renderScreen();

    await userEvent.click(screen.getByRole("button", { name: "Submit report" }));

    expect(await screen.findByText("Pick a reason")).toBeInTheDocument();
    expect(mutateAsync).not.toHaveBeenCalled();
  });

  it("shows why the backend refused the report", async () => {
    mutateAsync.mockRejectedValue(forbidden("already_reported"));
    renderScreen();

    await userEvent.click(screen.getByRole("radio", { name: /Abuse and harassment/ }));
    await userEvent.click(screen.getByRole("button", { name: "Submit report" }));

    expect(
      await screen.findByText("You have already reported this player in this game.")
    ).toBeInTheDocument();
  });
});
