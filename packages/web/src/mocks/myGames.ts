import type {
  KeyEnum,
  MyGame,
  MyGameSeats,
  MyGameState,
  MyGamesCurrent,
  PaginatedMyGameList,
} from "@/api/generated/endpoints";
import { gameFixtures, type GameFixtureName } from "./fixtures";

interface MyGameSpec {
  kind: MyGameState["kind"];
  deadline?: "phase" | "muster";
  result?: MyGameState["result"];
  winner?: string;
  departure?: MyGameState["departure"];
  seats?: MyGameSeats;
}

const myGame = (name: GameFixtureName, spec: MyGameSpec): MyGame => {
  const { game, totalUnreadMessageCount } = gameFixtures[name];
  const seat = game.members.find(m => m.isCurrentUser);
  const deadline =
    spec.deadline === "phase"
      ? game.currentPhase?.scheduledResolution ?? null
      : spec.deadline === "muster"
        ? game.musterDeadline
        : null;
  return {
    id: game.id,
    name: game.name,
    status: game.status,
    variantId: game.variantId,
    sandbox: game.sandbox,
    currentPhaseId: game.currentPhaseId,
    currentPhase: game.currentPhase,
    nation: game.sandbox ? null : seat?.nation ?? null,
    seats:
      spec.seats ??
      (game.status === "pending"
        ? { filled: game.members.length, total: 7 }
        : null),
    unreadCount: totalUnreadMessageCount,
    state: {
      kind: spec.kind,
      deadline,
      result: spec.result ?? null,
      winner: spec.winner ?? null,
      departure: spec.departure ?? null,
    },
  };
};

const currentSections: [KeyEnum, MyGame[]][] = [
  [
    "needs_attention",
    [
      myGame("musteringGame", {
        kind: "confirm_seat",
        deadline: "muster",
        seats: { filled: 4, total: 7 },
      }),
      myGame("activeGameWithdrawnPlayer", { kind: "submit_orders", deadline: "phase" }),
      myGame("activeGameDrawProposal", { kind: "vote_on_draw", deadline: "phase" }),
    ],
  ],
  [
    "managing",
    [
      myGame("activeGameMasterChat", { kind: "resolving", deadline: "phase" }),
      myGame("gameMasterMustering", {
        kind: "mustering",
        deadline: "muster",
        seats: { filled: 5, total: 7 },
      }),
      myGame("gameMasterGame", { kind: "waiting_for_players" }),
    ],
  ],
  [
    "active",
    [
      myGame("activeGameMovement", { kind: "orders_unconfirmed" }),
      myGame("activeGameNamedCoast", { kind: "orders_confirmed", deadline: "phase" }),
      myGame("activeGameSeatOpen", { kind: "resolving", deadline: "phase" }),
      myGame("activeGamePaused", { kind: "paused" }),
    ],
  ],
  [
    "mustering",
    [
      myGame("musteringGameConfirmed", {
        kind: "seat_confirmed",
        deadline: "muster",
        seats: { filled: 6, total: 7 },
      }),
    ],
  ],
  [
    "pending",
    [
      myGame("pendingGameAlmostFull", { kind: "waiting_for_players" }),
      myGame("pendingGameSomePlayers", { kind: "waiting_for_players" }),
    ],
  ],
  [
    "recently_finished",
    [myGame("finishedGameSolo", { kind: "finished", result: "solo_victory" })],
  ],
  ["sandbox", [myGame("sandboxGame", { kind: "sandbox" })]],
];

export const myGamesCurrent: MyGamesCurrent = {
  sections: currentSections.map(([key, games]) => ({ key, games })),
};

const finishedGames: MyGame[] = [
  myGame("activeGameEliminated", {
    kind: "finished",
    result: "ongoing",
    departure: "eliminated",
  }),
  myGame("activeGameWithdrawn", {
    kind: "finished",
    result: "ongoing",
    departure: "withdrawn",
  }),
  myGame("finishedGameSolo", { kind: "finished", result: "solo_victory" }),
  myGame("activeGameCivilDisorder", {
    kind: "finished",
    result: "ongoing",
    departure: "civil_disorder",
  }),
  myGame("finishedGameRemoved", {
    kind: "finished",
    result: "won_by",
    winner: "France",
    departure: "removed",
  }),
  myGame("finishedGameDraw", { kind: "finished", result: "draw" }),
  myGame("finishedGameAbandoned", { kind: "finished", result: "abandoned" }),
];

export const myGamesFinished: PaginatedMyGameList = {
  count: finishedGames.length,
  next: null,
  previous: null,
  results: finishedGames,
};
