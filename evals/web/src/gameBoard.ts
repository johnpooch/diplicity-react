import type { BoardState, GameOrder, GamePhase } from "./api";
import type { RenderState } from "./board/mapRenderer";
import { toRenderState } from "./board/toRenderState";
import { succeeded } from "./games";

const parentProvince = (province: string): string => province.split("/")[0];

export const gameRenderState = (phase: GamePhase): RenderState => {
  const dislodged = new Set(phase.dislodged.map(parentProvince));
  const board: BoardState = {
    id: phase.key,
    nation: "",
    phase: phase.phase,
    units: phase.units.map(unit =>
      dislodged.has(parentProvince(unit.province)) ? { ...unit, dislodged: true } : unit
    ),
    supply_centers: phase.supply_centers,
  };
  const byNation = new Map<string, GameOrder[]>();
  for (const order of phase.orders) {
    byNation.set(order.nation, [...(byNation.get(order.nation) ?? []), order]);
  }
  const orders = [...byNation].flatMap(([nation, own]) =>
    (toRenderState({ ...board, nation }, own).orders ?? []).map((state, index) =>
      succeeded(own[index].result) ? state : { ...state, failed: true }
    )
  );
  return { ...toRenderState(board, []), orders };
};
