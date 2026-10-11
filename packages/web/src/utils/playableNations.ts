import type { Nation } from "../api/generated/endpoints";

const countPlayableNations = (
  nations: readonly Pick<Nation, "nonPlayable">[]
): number => nations.filter(n => !n.nonPlayable).length;

export { countPlayableNations };
