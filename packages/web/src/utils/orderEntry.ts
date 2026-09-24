import type { GameRetrieve, PhaseRetrieve } from "../api/generated/endpoints";

const canEnterOrdersForPhase = (
  game: Pick<GameRetrieve, "status" | "currentPhaseId">,
  phase: Pick<PhaseRetrieve, "status">,
  selectedPhase: number
): boolean =>
  game.status === "active" &&
  phase.status === "active" &&
  game.currentPhaseId === selectedPhase;

export { canEnterOrdersForPhase };
