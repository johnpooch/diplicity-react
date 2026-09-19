import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { PhaseStepperTitle, PhaseStepperActions } from "./PhaseStepper";

const mockNavigate = vi.fn();

vi.mock("react-router", async () => {
  const actual = await vi.importActual("react-router");
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

const mockGameData = vi.fn();
const mockPhaseData = vi.fn();
const mockPhasesData = vi.fn();

vi.mock("@/api/generated/endpoints", () => ({
  useGameRetrieveSuspense: () => ({ data: mockGameData() }),
  useGamePhaseRetrieveSuspense: () => ({ data: mockPhaseData() }),
  useGamePhasesListSuspense: () => ({ data: mockPhasesData() }),
}));

if (!Element.prototype.hasPointerCapture)
  Element.prototype.hasPointerCapture = () => false;
if (!Element.prototype.releasePointerCapture)
  Element.prototype.releasePointerCapture = () => {};
if (!Element.prototype.scrollIntoView)
  Element.prototype.scrollIntoView = () => {};

const renderAtRoute = (element: React.ReactElement, path: string) =>
  render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path="/game/:gameId/phase/:phaseId" element={element} />
        <Route path="/game/:gameId/phase/:phaseId/:subRoute" element={element} />
      </Routes>
    </MemoryRouter>
  );

describe("PhaseStepperActions", () => {
  beforeEach(() => {
    mockNavigate.mockClear();
    mockPhaseData.mockReturnValue({
      name: "Spring 1901",
      status: "resolved",
      previousPhaseId: 4,
      nextPhaseId: 6,
      scheduledResolution: null,
      remainingTime: 0,
    });
  });

  it("navigates to the previous phase", async () => {
    renderAtRoute(<PhaseStepperActions />, "/game/1/phase/5");
    await userEvent.click(screen.getByLabelText("Previous phase"));
    expect(mockNavigate).toHaveBeenCalledWith("/game/1/phase/4");
  });

  it("navigates to the next phase, preserving the /orders suffix", async () => {
    renderAtRoute(<PhaseStepperActions />, "/game/1/phase/5/orders");
    await userEvent.click(screen.getByLabelText("Next phase"));
    expect(mockNavigate).toHaveBeenCalledWith("/game/1/phase/6/orders");
  });

  it("disables Previous at the first phase", () => {
    mockPhaseData.mockReturnValue({
      name: "Spring 1901",
      status: "resolved",
      previousPhaseId: null,
      nextPhaseId: 6,
      scheduledResolution: null,
      remainingTime: 0,
    });
    renderAtRoute(<PhaseStepperActions />, "/game/1/phase/1");
    expect(screen.getByLabelText("Previous phase")).toBeDisabled();
  });

  it("disables Next at the latest phase", () => {
    mockPhaseData.mockReturnValue({
      name: "Fall 1901",
      status: "active",
      previousPhaseId: 4,
      nextPhaseId: null,
      scheduledResolution: null,
      remainingTime: 0,
    });
    renderAtRoute(<PhaseStepperActions />, "/game/1/phase/6");
    expect(screen.getByLabelText("Next phase")).toBeDisabled();
  });
});

describe("PhaseStepperTitle", () => {
  beforeEach(() => {
    mockNavigate.mockClear();
    mockGameData.mockReturnValue({ isPaused: false, currentPhaseId: 6 });
    mockPhaseData.mockReturnValue({
      name: "Spring 1901",
      status: "completed",
      previousPhaseId: 4,
      nextPhaseId: 6,
      scheduledResolution: null,
      remainingTime: 0,
    });
    mockPhasesData.mockReturnValue([
      { id: 4, name: "Fall 1900", status: "completed" },
      { id: 5, name: "Spring 1901", status: "completed" },
      { id: 6, name: "Fall 1901", status: "active" },
    ]);
  });

  it("shows the viewed phase's name", () => {
    renderAtRoute(<PhaseStepperTitle />, "/game/1/phase/5");
    expect(screen.getByText("Spring 1901")).toBeInTheDocument();
  });

  it("shows Resolved for a historical phase", () => {
    renderAtRoute(<PhaseStepperTitle />, "/game/1/phase/5");
    expect(screen.getByText("Resolved")).toBeInTheDocument();
  });

  it("shows the remaining time and resolution label for the active phase", async () => {
    mockPhaseData.mockReturnValue({
      name: "Fall 1901",
      status: "active",
      previousPhaseId: 5,
      nextPhaseId: null,
      scheduledResolution: "2026-01-01T00:00:00Z",
      remainingTime: 3600,
    });
    renderAtRoute(<PhaseStepperTitle />, "/game/1/phase/6");
    expect(screen.queryByText("Resolved")).not.toBeInTheDocument();
    const remainingTime = screen.getByText("1h 0m remaining");
    expect(remainingTime).toHaveClass("block", "w-fit");

    await userEvent.hover(remainingTime);
    expect(await screen.findByRole("tooltip")).toHaveTextContent("Phase resolves");
  });

  it("opens a phase list marking the active phase Current, and navigates on selection", async () => {
    renderAtRoute(<PhaseStepperTitle />, "/game/1/phase/5");

    await userEvent.click(
      screen.getByRole("button", { name: /Spring 1901\. Choose phase/i })
    );

    const currentRow = screen.getByRole("button", { name: /Fall 1901/ });
    expect(within(currentRow).getByText("Current")).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: /Fall 1900/ }));
    expect(mockNavigate).toHaveBeenCalledWith("/game/1/phase/4");
  });
});
