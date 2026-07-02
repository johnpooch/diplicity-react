import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router";
import { describe, it, expect, vi } from "vitest";
import { LLMCallDetailScreen } from "./LLMCallDetail";

const mockCallData = vi.fn();

vi.mock("@/api/generated/endpoints", () => ({
  useLlmCallsRetrieveSuspense: () => ({ data: mockCallData() }),
  useUserRetrieveSuspense: () => ({ data: { name: "Reviewer", picture: null } }),
}));

const renderDetail = () =>
  render(
    <MemoryRouter initialEntries={["/llm-calls/1"]}>
      <Routes>
        <Route path="/llm-calls/:llmCallId" element={<LLMCallDetailScreen />} />
      </Routes>
    </MemoryRouter>
  );

describe("LLMCallDetail", () => {
  it("renders the system, input and output content", () => {
    mockCallData.mockReturnValue({
      id: 1,
      createdAt: "2026-05-01T10:00:01Z",
      stage: "plan",
      status: "success",
      model: "claude-haiku",
      gameId: "active-movement",
      phaseName: "Spring 1901, Movement",
      nation: "Germany",
      totalTokens: 1820,
      latencyMs: 2400,
      system: "You are Germany.",
      userContent: "Current board state",
      response: "My opening move",
      inputTokens: 1700,
      outputTokens: 120,
      cacheReadTokens: 1500,
      cacheWriteTokens: 200,
      errorMessage: "",
    });

    renderDetail();

    expect(screen.getByText("You are Germany.")).toBeInTheDocument();
    expect(screen.getByText("Current board state")).toBeInTheDocument();
    expect(screen.getByText("My opening move")).toBeInTheDocument();
    expect(screen.getByText("System")).toBeInTheDocument();
    expect(screen.getByText("Input")).toBeInTheDocument();
    expect(screen.getByText("Output")).toBeInTheDocument();
  });

  it("renders the error message for failed calls", () => {
    mockCallData.mockReturnValue({
      id: 3,
      createdAt: "2026-05-01T10:00:05Z",
      stage: "commit",
      status: "error",
      model: "claude-haiku",
      gameId: "active-movement",
      phaseName: "Spring 1901, Movement",
      nation: "Italy",
      totalTokens: 0,
      latencyMs: 500,
      system: "You are Italy.",
      userContent: "Confirm your orders.",
      response: "",
      inputTokens: 0,
      outputTokens: 0,
      cacheReadTokens: 0,
      cacheWriteTokens: 0,
      errorMessage: "Anthropic API timed out",
    });

    renderDetail();

    expect(screen.getByText("Error")).toBeInTheDocument();
    expect(screen.getByText("Anthropic API timed out")).toBeInTheDocument();
  });
});
