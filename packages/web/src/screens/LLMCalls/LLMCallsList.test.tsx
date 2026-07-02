import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router";
import { describe, it, expect, vi } from "vitest";
import { LLMCallsListScreen } from "./LLMCallsList";

const mockCallsData = vi.fn();

vi.mock("@/api/generated/endpoints", () => ({
  useLlmCallsListSuspense: () => ({ data: mockCallsData() }),
  useUserRetrieveSuspense: () => ({ data: { name: "Reviewer", picture: null } }),
}));

const renderList = (initialEntry: string) =>
  render(
    <MemoryRouter initialEntries={[initialEntry]}>
      <Routes>
        <Route path="/llm-calls" element={<LLMCallsListScreen />} />
      </Routes>
    </MemoryRouter>
  );

describe("LLMCallsList", () => {
  it("renders a row per call with stage, nation and a link to the detail", () => {
    mockCallsData.mockReturnValue([
      {
        id: 7,
        createdAt: "2026-05-01T10:00:01Z",
        stage: "plan",
        status: "success",
        model: "claude-haiku",
        gameId: "active-movement",
        phaseName: "Spring 1901, Movement",
        nation: "Germany",
        channelNations: [],
        totalTokens: 1820,
        latencyMs: 2400,
      },
    ]);

    renderList("/llm-calls?game=active-movement");

    expect(screen.getByText("plan")).toBeInTheDocument();
    expect(screen.getByText("Germany")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Germany/ })).toHaveAttribute(
      "href",
      "/llm-calls/7"
    );
  });

  it("shows who a reply is addressed to", () => {
    mockCallsData.mockReturnValue([
      {
        id: 9,
        createdAt: "2026-05-01T10:00:03Z",
        stage: "reply",
        status: "success",
        model: "claude-haiku",
        gameId: "active-movement",
        phaseName: "Spring 1901, Movement",
        nation: "Germany",
        channelNations: ["Italy"],
        totalTokens: 640,
        latencyMs: 1800,
      },
    ]);

    renderList("/llm-calls?game=active-movement");

    expect(screen.getByText(/→ Italy/)).toBeInTheDocument();
  });

  it("shows an error badge for failed calls", () => {
    mockCallsData.mockReturnValue([
      {
        id: 8,
        createdAt: "2026-05-01T10:00:05Z",
        stage: "commit",
        status: "error",
        model: "claude-haiku",
        gameId: "active-movement",
        phaseName: "Spring 1901, Movement",
        nation: "Italy",
        channelNations: [],
        totalTokens: 0,
        latencyMs: 500,
      },
    ]);

    renderList("/llm-calls?game=active-movement");

    expect(screen.getByText("error")).toBeInTheDocument();
  });

  it("renders an empty state when there are no calls", () => {
    mockCallsData.mockReturnValue([]);

    renderList("/llm-calls");

    expect(screen.getByText("No LLM calls")).toBeInTheDocument();
  });
});
