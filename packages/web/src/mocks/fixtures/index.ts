import type { GameFixture } from "./types";
import {
  activeGameBuild,
  activeGameDrawProposal,
  activeGameMovement,
  activeGameNamedCoast,
  activeGameRetreat,
  activeGameRetreatWindowClosed,
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
export { currentUserProfile, publicProfiles } from "./users";

export const gameFixtures = {
  pendingGameNoPlayers,
  pendingGameSomePlayers,
  pendingGameAlmostFull,
  activeGameMovement,
  activeGameNamedCoast,
  activeGameRetreat,
  activeGameRetreatWindowClosed,
  activeGameBuild,
  activeGameDrawProposal,
  finishedGameSolo,
  finishedGameDraw,
  gameMasterGame,
  gameNotJoined,
} satisfies Record<string, GameFixture>;

export type GameFixtureName = keyof typeof gameFixtures;

export const fixtureByGameId: Record<string, GameFixture> = Object.fromEntries(
  Object.values(gameFixtures).map(fixture => [fixture.game.id, fixture])
);
