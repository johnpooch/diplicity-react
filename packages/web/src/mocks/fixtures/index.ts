import type { GameFixture } from "./types";
import {
  activeGameBuild,
  activeGameCivilDisorder,
  activeGameDrawProposal,
  activeGameEliminated,
  activeGameMasterChat,
  activeGameMovement,
  activeGameNamedCoast,
  activeGamePaused,
  activeGameRetreat,
  activeGameSeatOpen,
  activeGameSeatOpenLocked,
  activeGameSeatOpenSpectator,
  activeGameWithdrawn,
  activeGameWithdrawnPlayer,
  finishedGameAbandoned,
  finishedGameDraw,
  finishedGameRemoved,
  finishedGameSolo,
  gameMasterGame,
  gameMasterMustering,
  gameNotJoined,
  musteringGame,
  musteringGameConfirmed,
  pendingGameAlmostFull,
  pendingGameCommitted,
  pendingGameCommittedLocked,
  pendingGameFastestStart,
  pendingGameNoPlayers,
  pendingGameShortPhases,
  pendingGameSomePlayers,
  sandboxGame,
} from "./games";

export type { GameFixture } from "./types";
export { classicalVariant, classicalProvinces, nation, province } from "./classical";
export { allVariants, extraVariants, draftVariant } from "./variants";
export { botRoster, currentUserProfile, makeBotMember, makeMember, publicProfiles } from "./users";

export const gameFixtures = {
  pendingGameNoPlayers,
  pendingGameSomePlayers,
  pendingGameAlmostFull,
  pendingGameCommitted,
  pendingGameCommittedLocked,
  pendingGameFastestStart,
  pendingGameShortPhases,
  musteringGame,
  musteringGameConfirmed,
  gameMasterMustering,
  activeGameMovement,
  activeGameNamedCoast,
  activeGameRetreat,
  activeGameBuild,
  activeGameDrawProposal,
  activeGamePaused,
  activeGameEliminated,
  activeGameCivilDisorder,
  activeGameWithdrawnPlayer,
  activeGameWithdrawn,
  activeGameMasterChat,
  activeGameSeatOpen,
  activeGameSeatOpenSpectator,
  activeGameSeatOpenLocked,
  finishedGameSolo,
  finishedGameDraw,
  finishedGameRemoved,
  finishedGameAbandoned,
  gameMasterGame,
  gameNotJoined,
  sandboxGame,
} satisfies Record<string, GameFixture>;

export type GameFixtureName = keyof typeof gameFixtures;

export const fixtureByGameId: Record<string, GameFixture> = Object.fromEntries(
  Object.values(gameFixtures).map(fixture => [fixture.game.id, fixture])
);
