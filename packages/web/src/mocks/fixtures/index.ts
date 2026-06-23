import type { GameFixture } from "./types";
import {
  activeGameBuild,
  activeGameDrawProposal,
  activeGameEliminated,
  activeGameMovement,
  activeGameNamedCoast,
  activeGameRetreat,
  finishedGameDraw,
  finishedGameSolo,
  gameMasterGame,
  gameNotJoined,
  pendingGameAlmostFull,
  pendingGameNoPlayers,
  pendingGameSomePlayers,
} from "./games";

export type { GameFixture } from "./types";
export { classicalVariant, classicalProvinces, nation, province } from "./classical";
export { allVariants, extraVariants } from "./variants";
export { currentUserProfile, publicProfiles } from "./users";

export const gameFixtures = {
  pendingGameNoPlayers,
  pendingGameSomePlayers,
  pendingGameAlmostFull,
  activeGameMovement,
  activeGameNamedCoast,
  activeGameRetreat,
  activeGameBuild,
  activeGameDrawProposal,
  activeGameEliminated,
  finishedGameSolo,
  finishedGameDraw,
  gameMasterGame,
  gameNotJoined,
} satisfies Record<string, GameFixture>;

export type GameFixtureName = keyof typeof gameFixtures;

export const fixtureByGameId: Record<string, GameFixture> = Object.fromEntries(
  Object.values(gameFixtures).map(fixture => [fixture.game.id, fixture])
);
