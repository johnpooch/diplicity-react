import type { FlatOrderOption, PhaseState } from "../api/generated/endpoints";

const filterOrderableOptions = (
  options: readonly FlatOrderOption[],
  phaseStates: readonly PhaseState[]
): FlatOrderOption[] => {
  const orderable = new Set(
    phaseStates.flatMap(ps => ps.orderableProvinces.map(p => p.id))
  );
  return options.filter(o => !!o.source && orderable.has(o.source.id));
};

export { filterOrderableOptions };
