import type { Order, PhaseRetrieve } from "@/api/generated/endpoints";

export type Board = {
  phase: PhaseRetrieve;
  orders: Order[];
};

export type StepGoal =
  | { kind: "continue" }
  | { kind: "select"; province: string }
  // A move is built source → target; a support adds an intermediate tap on the
  // supported unit (aux), so the chain is source → aux → target.
  | { kind: "order"; source: string; target: string; aux?: string }
  | { kind: "confirm" }
  | { kind: "chat" };

export type ScriptedMessage = {
  from: "you" | "ally";
  body: string;
};

export type TutorialStep = {
  coach: string;
  title?: string;
  goal: StepGoal;
  highlight?: string[];
  tappable?: string[];
  focus?: string[];
  primaryLabel?: string;
  order?: Order;
  resolvedBoard?: Board;
  // Board applied when this step becomes active (e.g. an ally's order appearing).
  enterBoard?: Board;
  // Scripted conversation for chat steps; `ally` is the variant nation id.
  chat?: ScriptedMessage[];
  ally?: string;
};

export type Lesson = {
  id: string;
  title: string;
  initialBoard: Board;
  focus?: string[];
  steps: TutorialStep[];
};
