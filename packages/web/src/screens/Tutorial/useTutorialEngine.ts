import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Map as MapIcon, MessageCircle } from "lucide-react";
import { unitAbbrev } from "@/utils/buildOrderProgressText";
import type { NavigationItemType } from "@/components/Navigation";
import { provinceName } from "./lessons";
import type { Board, Lesson, TutorialStep } from "./types";

export type TutorialView = "map" | "chat";

export type PrimaryAction = { label: string; run: () => void };

export type TutorialEngine = {
  lesson: Lesson;
  step: TutorialStep;
  board: Board;
  selected: string[];
  highlighted: string[];
  tappable: string[];
  focus: string[];
  bannerText: string | null;
  primaryAction: PrimaryAction | null;
  isFirstStep: boolean;
  finished: boolean;
  view: TutorialView;
  setView: (view: TutorialView) => void;
  showNav: boolean;
  navItems: NavigationItemType[];
  progress: {
    lessonIndex: number;
    lessonCount: number;
    stepIndex: number;
    stepCount: number;
    lessonTitle: string;
  };
  onProvinceClick: (province: string) => void;
  skip: () => void;
  restart: () => void;
};

// The ordered provinces the player must tap to build an order: a move is
// source → target; a support is source → aux (supported unit) → target.
function orderSequence(step: TutorialStep): string[] {
  if (step.goal.kind !== "order") return [];
  const { source, aux, target } = step.goal;
  return aux ? [source, aux, target] : [source, target];
}

function defaultTappable(step: TutorialStep): string[] {
  if (step.tappable) return step.tappable;
  switch (step.goal.kind) {
    case "select":
      return [step.goal.province];
    case "order":
      return orderSequence(step);
    default:
      return [];
  }
}

export function useTutorialEngine(lessons: Lesson[]): TutorialEngine {
  const [lessonIndex, setLessonIndex] = useState(0);
  const [stepIndex, setStepIndex] = useState(0);
  const [board, setBoard] = useState<Board>(lessons[0].initialBoard);
  const [selected, setSelected] = useState<string[]>([]);
  const [orderProgress, setOrderProgress] = useState(0);
  const [finished, setFinished] = useState(false);
  const [view, setView] = useState<TutorialView>("map");
  const [transientBanner, setTransientBanner] = useState<string | null>(null);
  const bannerTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    return () => {
      if (bannerTimer.current) clearTimeout(bannerTimer.current);
    };
  }, []);

  // A short-lived banner, mirroring the real map's tap feedback.
  const showBanner = useCallback((text: string) => {
    if (bannerTimer.current) clearTimeout(bannerTimer.current);
    setTransientBanner(text);
    bannerTimer.current = setTimeout(() => setTransientBanner(null), 3000);
  }, []);

  const lesson = lessons[lessonIndex];
  const step = lesson.steps[stepIndex];

  const goToLesson = useCallback(
    (index: number) => {
      setLessonIndex(index);
      setStepIndex(0);
      setBoard(lessons[index].initialBoard);
      setSelected([]);
      setOrderProgress(0);
      setView("map");
    },
    [lessons]
  );

  const advance = useCallback(() => {
    setSelected([]);
    setOrderProgress(0);
    setView("map");
    if (stepIndex + 1 < lesson.steps.length) {
      const nextStep = lesson.steps[stepIndex + 1];
      if (nextStep.enterBoard) setBoard(nextStep.enterBoard);
      setStepIndex(stepIndex + 1);
    } else if (lessonIndex + 1 < lessons.length) {
      goToLesson(lessonIndex + 1);
    } else {
      setFinished(true);
    }
  }, [stepIndex, lesson.steps, lessonIndex, lessons.length, goToLesson]);

  const restart = useCallback(() => {
    setFinished(false);
    goToLesson(0);
  }, [goToLesson]);

  const skip = useCallback(() => {
    setFinished(true);
  }, []);

  const onProvinceClick = useCallback(
    (province: string) => {
      if (step.goal.kind === "select") {
        if (province === step.goal.province) {
          const unit = board.phase.units.find(
            u => u.province.id === province
          );
          showBanner(
            unit
              ? `${unitAbbrev(unit.type)} ${unit.province.name} (${unit.nation.name})`
              : provinceName(province)
          );
          setSelected([province]);
          advance();
        }
        return;
      }
      if (step.goal.kind === "order") {
        const seq = orderSequence(step);
        if (province !== seq[orderProgress]) return;
        const next = orderProgress + 1;
        if (next < seq.length) {
          setOrderProgress(next);
          setSelected(seq.slice(0, next));
          return;
        }
        if (step.order) {
          const newOrder = step.order;
          setBoard(prev => ({
            ...prev,
            orders: [
              ...prev.orders.filter(o => o.source.id !== newOrder.source.id),
              newOrder,
            ],
          }));
        }
        advance();
      }
    },
    [step, orderProgress, advance, board, showBanner]
  );

  const primaryAction = useMemo<PrimaryAction | null>(() => {
    if (step.goal.kind === "continue" || step.goal.kind === "chat") {
      return { label: step.primaryLabel ?? "Continue", run: advance };
    }
    if (step.goal.kind === "confirm") {
      return {
        label: step.primaryLabel ?? "Confirm your order",
        run: () => {
          if (step.resolvedBoard) setBoard(step.resolvedBoard);
          advance();
        },
      };
    }
    return null;
  }, [step, advance]);

  // For move orders, mirror the real game: highlight the unit first, then only
  // the valid destination once the unit is selected.
  // The Map / Chat navigation appears only while chatting is relevant.
  const showNav = step.goal.kind === "chat";
  const navItems = useMemo<NavigationItemType[]>(
    () => [
      { label: "Map", icon: MapIcon, path: "map", isActive: view === "map" },
      {
        label: "Chat",
        icon: MessageCircle,
        path: "chat",
        isActive: view === "chat",
        badge: view === "map" ? "•" : undefined,
      },
    ],
    [view]
  );

  // While building an order, highlight only the next province the player must
  // tap (source, then the supported unit for a support, then the destination).
  const nextOrderTap = useMemo(() => {
    if (step.goal.kind !== "order") return null;
    return orderSequence(step)[orderProgress] ?? null;
  }, [step, orderProgress]);

  const highlighted = useMemo(() => {
    if (step.goal.kind === "order") {
      return nextOrderTap ? [nextOrderTap] : [];
    }
    return step.highlight ?? [];
  }, [step, nextOrderTap]);

  const tappable = useMemo(() => {
    if (step.goal.kind === "order") {
      return nextOrderTap ? [nextOrderTap] : [];
    }
    return defaultTappable(step);
  }, [step, nextOrderTap]);

  const focus = useMemo(
    () => step.focus ?? lesson.focus ?? [],
    [step, lesson]
  );

  // Mirror the real map's order-progress banner while an order is being built,
  // falling back to the short-lived tap feedback banner.
  const bannerText = useMemo(() => {
    if (step.goal.kind === "order" && step.order && orderProgress >= 1) {
      const { unitType, source, orderType } = step.order;
      const verb = orderType === "Support" ? "Support to" : "Move to";
      return `${unitAbbrev(unitType)} ${source.name} ${verb} ...`;
    }
    return transientBanner;
  }, [step, orderProgress, transientBanner]);

  return {
    lesson,
    step,
    board,
    selected,
    highlighted,
    tappable,
    focus,
    bannerText,
    primaryAction,
    isFirstStep: lessonIndex === 0 && stepIndex === 0,
    finished,
    view,
    setView,
    showNav,
    navItems,
    progress: {
      lessonIndex,
      lessonCount: lessons.length,
      stepIndex,
      stepCount: lesson.steps.length,
      lessonTitle: lesson.title,
    },
    onProvinceClick,
    skip,
    restart,
  };
}
