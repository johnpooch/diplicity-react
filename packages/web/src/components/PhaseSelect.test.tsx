import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { PhaseSelect } from "./PhaseSelect";

const mockNavigate = vi.fn();

vi.mock("react-router", async () => {
  const actual = await vi.importActual("react-router");
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

vi.mock("@/api/generated/endpoints", () => ({
  useGameRetrieveSuspense: () => ({
    data: { isPaused: false },
  }),
  useGamePhaseRetrieveSuspense: () => ({
    data: {
      name: "Spring 1901",
      status: "resolved",
      previousPhaseId: 4,
      nextPhaseId: 6,
      scheduledResolution: null,
      remainingTime: 0,
    },
  }),
}));

const renderAtRoute = (path: string) =>
  render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path="/game/:gameId/phase/:phaseId" element={<PhaseSelect />} />
        <Route
          path="/game/:gameId/phase/:phaseId/:subRoute"
          element={<PhaseSelect />}
        />
      </Routes>
    </MemoryRouter>
  );

describe("PhaseSelect", () => {
  beforeEach(() => {
    mockNavigate.mockClear();
  });

  describe("phase navigation from index route (map screen)", () => {
    it("navigates to previous phase on index route", async () => {
      renderAtRoute("/game/1/phase/5");
      await userEvent.click(screen.getByLabelText("Previous phase"));
      expect(mockNavigate).toHaveBeenCalledWith("/game/1/phase/4");
    });

    it("navigates to next phase on index route", async () => {
      renderAtRoute("/game/1/phase/5");
      await userEvent.click(screen.getByLabelText("Next phase"));
      expect(mockNavigate).toHaveBeenCalledWith("/game/1/phase/6");
    });
  });

  describe("phase navigation from sub-routes", () => {
    it("navigates to previous phase preserving /orders suffix", async () => {
      renderAtRoute("/game/1/phase/5/orders");
      await userEvent.click(screen.getByLabelText("Previous phase"));
      expect(mockNavigate).toHaveBeenCalledWith("/game/1/phase/4/orders");
    });

    it("navigates to next phase preserving /chat suffix", async () => {
      renderAtRoute("/game/1/phase/5/chat");
      await userEvent.click(screen.getByLabelText("Next phase"));
      expect(mockNavigate).toHaveBeenCalledWith("/game/1/phase/6/chat");
    });
  });
});
