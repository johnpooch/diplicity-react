import { act, renderHook } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import type {
  Nation,
  Order,
  PhaseRetrieve,
  Province,
  Unit,
} from "@/api/generated/endpoints";
import type { Board, Lesson } from "./types";
import { useTutorialEngine } from "./useTutorialEngine";

const prov = (id: string): Province => ({
  id,
  name: id,
  type: "land",
  supplyCenter: false,
  parentId: null,
  namedCoastIds: [],
});

const nation = (nationId: string): Nation => ({
  nationId,
  name: nationId,
  color: "#ffffff",
  nonPlayable: false,
  flagUrl: null,
});

const phase = (units: Unit[] = []): PhaseRetrieve => ({
  id: 1,
  ordinal: 1,
  season: "Spring",
  year: 1901,
  name: "Spring 1901",
  type: "Movement",
  remainingTime: 0,
  scheduledResolution: "2026-01-01T00:00:00Z",
  status: "active",
  units,
  supplyCenters: [],
  previousPhaseId: null,
  nextPhaseId: null,
  provinceNations: "",
});

const unit = (provinceId: string): Unit => ({
  type: "Army",
  nation: nation("france"),
  province: prov(provinceId),
  dislodged: false,
  dislodgedBy: null,
});

const order = (
  source: string,
  target: string | null,
  aux: string | null = null
): Order => ({
  source: prov(source),
  sourceCoast: null,
  target: (target ? prov(target) : null) as Order["target"],
  aux: (aux ? prov(aux) : null) as Order["aux"],
  targetCoast: null,
  namedCoast: null as unknown as Order["namedCoast"],
  resolution: { status: "Succeeded", by: null },
  options: [],
  orderType: "Move",
  unitType: "Army",
  nation: nation("france"),
  complete: true,
  step: "completed",
  title: "t",
  summary: "t",
});

const emptyBoard: Board = { phase: phase(), orders: [] };
const resolvedBoard: Board = { phase: phase([unit("bbb")]), orders: [order("aaa", "bbb")] };
const selectEnterBoard: Board = { phase: phase([unit("fff")]), orders: [] };

function buildLessons(): Lesson[] {
  return [
    {
      id: "l1",
      title: "L1",
      initialBoard: emptyBoard,
      steps: [
        { coach: "c0", goal: { kind: "continue" }, primaryLabel: "Start" },
        {
          coach: "c1",
          goal: { kind: "order", source: "aaa", target: "bbb" },
          order: order("aaa", "bbb"),
        },
        { coach: "c2", goal: { kind: "confirm" }, resolvedBoard },
        { coach: "c3", goal: { kind: "continue" }, primaryLabel: "Next" },
      ],
    },
    {
      id: "l2",
      title: "L2",
      initialBoard: emptyBoard,
      steps: [
        {
          coach: "s0",
          goal: { kind: "order", source: "ccc", aux: "ddd", target: "eee" },
          order: order("ccc", "eee", "ddd"),
        },
        {
          coach: "s1",
          goal: { kind: "chat" },
          ally: "england",
          chat: [{ from: "you", body: "hi" }],
          primaryLabel: "Back",
        },
        {
          coach: "s2",
          goal: { kind: "select", province: "fff" },
          enterBoard: selectEnterBoard,
        },
      ],
    },
  ];
}

function setup() {
  return renderHook(() => useTutorialEngine(buildLessons()));
}

describe("useTutorialEngine", () => {
  it("starts on the first step of the first lesson", () => {
    const { result } = setup();
    expect(result.current.lesson.id).toBe("l1");
    expect(result.current.step.coach).toBe("c0");
    expect(result.current.isFirstStep).toBe(true);
    expect(result.current.finished).toBe(false);
    expect(result.current.primaryAction?.label).toBe("Start");
    expect(result.current.progress.stepCount).toBe(4);
    expect(result.current.progress.lessonCount).toBe(2);
  });

  it("advances a continue step via its primary action", () => {
    const { result } = setup();
    act(() => result.current.primaryAction!.run());
    expect(result.current.step.goal.kind).toBe("order");
    expect(result.current.primaryAction).toBeNull();
    expect(result.current.highlighted).toEqual(["aaa"]);
    expect(result.current.tappable).toEqual(["aaa"]);
  });

  it("builds a move order tap by tap and ignores wrong taps", () => {
    const { result } = setup();
    act(() => result.current.primaryAction!.run());

    act(() => result.current.onProvinceClick("zzz"));
    expect(result.current.selected).toEqual([]);
    expect(result.current.tappable).toEqual(["aaa"]);

    act(() => result.current.onProvinceClick("aaa"));
    expect(result.current.selected).toEqual(["aaa"]);
    expect(result.current.tappable).toEqual(["bbb"]);
    expect(result.current.bannerText).toMatch(/aaa/);

    act(() => result.current.onProvinceClick("bbb"));
    expect(result.current.step.goal.kind).toBe("confirm");
    expect(result.current.board.orders).toHaveLength(1);
    expect(result.current.board.orders[0].source.id).toBe("aaa");
  });

  it("applies resolvedBoard when confirming", () => {
    const { result } = setup();
    act(() => result.current.primaryAction!.run());
    act(() => result.current.onProvinceClick("aaa"));
    act(() => result.current.onProvinceClick("bbb"));

    act(() => result.current.primaryAction!.run());
    expect(result.current.step.coach).toBe("c3");
    expect(result.current.board.phase.units).toHaveLength(1);
    expect(result.current.board.phase.units[0].province.id).toBe("bbb");
  });

  it("crosses into the next lesson and resets to its initial board", () => {
    const { result } = setup();
    act(() => result.current.primaryAction!.run());
    act(() => result.current.onProvinceClick("aaa"));
    act(() => result.current.onProvinceClick("bbb"));
    act(() => result.current.primaryAction!.run());

    act(() => result.current.primaryAction!.run());
    expect(result.current.lesson.id).toBe("l2");
    expect(result.current.step.coach).toBe("s0");
    expect(result.current.board.orders).toHaveLength(0);
  });

  it("builds a support order through the supported unit", () => {
    const { result } = goToSupportStep();
    expect(result.current.tappable).toEqual(["ccc"]);

    act(() => result.current.onProvinceClick("ccc"));
    expect(result.current.tappable).toEqual(["ddd"]);
    act(() => result.current.onProvinceClick("ddd"));
    expect(result.current.tappable).toEqual(["eee"]);
    act(() => result.current.onProvinceClick("eee"));

    expect(result.current.step.goal.kind).toBe("chat");
  });

  it("shows navigation and switches views on chat steps", () => {
    const { result } = goToSupportStep();
    act(() => result.current.onProvinceClick("ccc"));
    act(() => result.current.onProvinceClick("ddd"));
    act(() => result.current.onProvinceClick("eee"));

    expect(result.current.showNav).toBe(true);
    expect(result.current.navItems).toHaveLength(2);
    expect(result.current.view).toBe("map");
    expect(result.current.primaryAction?.label).toBe("Back");

    act(() => result.current.setView("chat"));
    expect(result.current.view).toBe("chat");
  });

  it("applies enterBoard when advancing into a step and finishes on the last step", () => {
    const { result } = goToSupportStep();
    act(() => result.current.onProvinceClick("ccc"));
    act(() => result.current.onProvinceClick("ddd"));
    act(() => result.current.onProvinceClick("eee"));
    act(() => result.current.primaryAction!.run());

    expect(result.current.step.goal.kind).toBe("select");
    expect(result.current.board.phase.units).toHaveLength(1);
    expect(result.current.board.phase.units[0].province.id).toBe("fff");

    act(() => result.current.onProvinceClick("zzz"));
    expect(result.current.finished).toBe(false);

    act(() => result.current.onProvinceClick("fff"));
    expect(result.current.finished).toBe(true);
  });

  it("skips straight to finished and restarts back to the beginning", () => {
    const { result } = setup();
    act(() => result.current.skip());
    expect(result.current.finished).toBe(true);

    act(() => result.current.restart());
    expect(result.current.finished).toBe(false);
    expect(result.current.lesson.id).toBe("l1");
    expect(result.current.step.coach).toBe("c0");
  });
});

function goToSupportStep() {
  const rendered = setup();
  const { result } = rendered;
  act(() => result.current.primaryAction!.run());
  act(() => result.current.onProvinceClick("aaa"));
  act(() => result.current.onProvinceClick("bbb"));
  act(() => result.current.primaryAction!.run());
  act(() => result.current.primaryAction!.run());
  return rendered;
}
