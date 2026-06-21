import type { DrawProposal, Member } from "@/api/generated/endpoints";
import {
  futureIso,
  makeChannel,
  makeFixture,
  makeGame,
  makeMessage,
  makeOrder,
  makePhase,
  makePhaseState,
  makeSupplyCenter,
  makeUnit,
} from "./builders";
import { classicalStartSupplyCenters, classicalStartUnits } from "./classical";
import { makeMember, players } from "./users";

const NATION_ASSIGNMENT: [number, string][] = [
  [0, "England"],
  [1, "Austria"],
  [2, "France"],
  [3, "Germany"],
  [4, "Italy"],
  [5, "Russia"],
  [6, "Turkey"],
];

const makeActiveMembers = (): Member[] =>
  NATION_ASSIGNMENT.map(([playerIndex, nation]) =>
    makeMember(players[playerIndex], nation, {
      isGameCreator: playerIndex === 1,
    })
  );

const makePendingMembers = (count: number, includeCurrentUser = true): Member[] => {
  const seeds = includeCurrentUser ? players : players.slice(1);
  return seeds
    .slice(0, count)
    .map((player, index) =>
      makeMember(player, null, { isGameCreator: index === 0 })
    );
};

export const pendingGameNoPlayers = makeFixture({
  description:
    "Pending public game with zero members. The current user can join it.",
  game: makeGame("pending-no-players", "Fresh Open Game", [], [], {
    status: "pending",
    canJoin: true,
    movementPhaseDuration: "48 hours",
  }),
});

export const pendingGameSomePlayers = makeFixture({
  description:
    "Pending game with 3 of 7 players, including the current user (who created it). Nations are not assigned yet.",
  game: makeGame(
    "pending-some-players",
    "Gathering Forces",
    makePendingMembers(3),
    [],
    {
      status: "pending",
      canLeave: true,
      canDelete: true,
    }
  ),
});

export const pendingGameAlmostFull = makeFixture({
  description:
    "Pending game with 6 of 7 players including the current user — one seat left before it starts.",
  game: makeGame(
    "pending-almost-full",
    "One Seat Left",
    makePendingMembers(6),
    [],
    {
      status: "pending",
      canLeave: true,
    }
  ),
});

export const gameMasterGame = makeFixture({
  description:
    "Pending private game run by a non-playing Game Master (the current user). The GM holds the management powers, takes no nation, and appears at the top of the player roster.",
  game: makeGame(
    "game-master",
    "Master of Ceremonies",
    players.slice(1, 4).map(player => makeMember(player, null)),
    [],
    {
      status: "pending",
      private: true,
      canManage: true,
      canDelete: true,
      gameMaster: { userId: 1, name: "Mock Player", picture: null },
    }
  ),
});

const buildActiveMovement = () => {
  const members = makeActiveMembers();
  const phase = makePhase(101, 1, { remainingTime: 22 * 60 * 60 });
  const channels = [
    makeChannel("Public Press", members, [
      makeMessage(members[1], "Good luck everyone!", "2026-05-01T11:00:00Z"),
      makeMessage(members[2], "May the best diplomat win.", "2026-05-01T11:05:00Z"),
    ]),
    makeChannel(
      "England, France",
      [members[0], members[2]],
      [
        makeMessage(
          members[2],
          "Shall we agree the Channel stays empty this year?",
          "2026-05-01T12:00:00Z"
        ),
        makeMessage(
          members[0],
          "Agreed — I'm heading north anyway.",
          "2026-05-01T12:10:00Z"
        ),
      ],
      { unreadMessageCount: 1 }
    ),
  ];
  return makeFixture({
    description:
      "Active game in the Spring 1901 movement phase. The current user (England) has entered 2 of 3 orders. Includes public and private chat channels.",
    game: makeGame("active-movement", "Spring Awakening", members, [phase], {
      orderStatus: "orders_required",
      memberStatus: [],
    }),
    phases: [phase],
    ordersByPhase: {
      101: [
        makeOrder({
          nationId: "england",
          unitType: "Fleet",
          orderType: "Move",
          source: "lon",
          target: "nth",
        }),
        makeOrder({
          nationId: "england",
          unitType: "Fleet",
          orderType: "Move",
          source: "edi",
          target: "nrg",
        }),
      ],
    },
    phaseStates: [
      makePhaseState(members[0], ["lon", "edi", "lvp"]),
      makePhaseState(members[1], ["vie", "bud", "tri"], { ordersConfirmed: true }),
      makePhaseState(members[2], ["par", "mar", "bre"]),
      makePhaseState(members[3], ["ber", "mun", "kie"], { ordersConfirmed: true }),
      makePhaseState(members[4], ["rom", "ven", "nap"]),
      makePhaseState(members[5], ["mos", "stp", "war", "sev"]),
      makePhaseState(members[6], ["con", "ank", "smy"]),
    ],
    channels,
    totalUnreadMessageCount: 1,
  });
};

export const activeGameMovement = buildActiveMovement();

const buildActiveNamedCoast = () => {
  const members = makeActiveMembers();
  const phase = makePhase(901, 1, {
    remainingTime: 20 * 60 * 60,
    units: [
      ...classicalStartUnits.filter(
        u =>
          u.nation.name !== "England" &&
          u.province.id !== "stp" &&
          u.province.id !== "stp/sc"
      ),
      makeUnit("Fleet", "england", "por"),
      makeUnit("Fleet", "england", "mid"),
      makeUnit("Fleet", "england", "stp/nc"),
      makeUnit("Fleet", "england", "nwy"),
    ],
  });
  return makeFixture({
    description:
      "Active movement phase showcasing named coasts. The current user (England) has a fleet on St. Petersburg (NC) supporting a move, a fleet supporting another into Spain (NC), and a fleet moving onto Spain's north coast. Used to verify orders and the map render the correct coast.",
    game: makeGame("active-named-coast", "Iberian Gambit", members, [phase]),
    phases: [phase],
    ordersByPhase: {
      901: [
        makeOrder({
          nationId: "england",
          unitType: "Fleet",
          orderType: "Move",
          source: "por",
          target: "spa",
          namedCoast: "spa/nc",
          summary: "Move to Spain (NC)",
        }),
        makeOrder({
          nationId: "england",
          unitType: "Fleet",
          orderType: "Support",
          source: "mid",
          aux: "por",
          target: "spa",
          targetCoast: "spa/nc",
          summary: "Support Portugal to Spain (NC)",
        }),
        makeOrder({
          nationId: "england",
          unitType: "Fleet",
          orderType: "Support",
          source: "stp",
          sourceCoast: "stp/nc",
          aux: "nwy",
          target: "bar",
          summary: "Support Norway to Barents Sea",
        }),
        makeOrder({
          nationId: "england",
          unitType: "Fleet",
          orderType: "Move",
          source: "nwy",
          target: "bar",
          summary: "Move to Barents Sea",
        }),
      ],
    },
    phaseStates: [
      makePhaseState(members[0], ["por", "mid", "stp", "nwy"]),
      makePhaseState(members[2], ["par", "mar", "bre"]),
      makePhaseState(members[5], ["mos", "war", "sev"]),
    ],
    channels: [makeChannel("Public Press", members, [])],
    totalUnreadMessageCount: 0,
  });
};

export const activeGameNamedCoast = buildActiveNamedCoast();

const buildActiveRetreat = () => {
  const members = makeActiveMembers();
  const springUnits = classicalStartUnits.map(u => {
    if (u.province.id === "lon") return makeUnit("Fleet", "england", "nth");
    if (u.province.id === "edi") return makeUnit("Fleet", "england", "nrg");
    if (u.province.id === "lvp") return makeUnit("Army", "england", "yor");
    if (u.province.id === "kie") return makeUnit("Fleet", "germany", "den");
    if (u.province.id === "ber") return makeUnit("Army", "germany", "kie");
    return u;
  });
  const fallUnits = springUnits.map(u => {
    if (u.province.id === "yor")
      return makeUnit("Army", "england", "nwy", {
        dislodged: true,
        dislodgedBy: { type: "Army", nation: "Russia", province: "nwy" },
      });
    if (u.province.id === "stp") return makeUnit("Army", "russia", "nwy");
    return u;
  });
  const spring = makePhase(201, 1, { status: "completed", nextPhaseId: 202 });
  const fallMove = makePhase(202, 2, {
    season: "Fall",
    status: "completed",
    units: springUnits,
    previousPhaseId: 201,
    nextPhaseId: 203,
  });
  const retreat = makePhase(203, 3, {
    season: "Fall",
    type: "Retreat",
    remainingTime: 10 * 60 * 60,
    units: fallUnits,
    previousPhaseId: 202,
  });
  return makeFixture({
    description:
      "Active game in a Fall 1901 retreat phase. The current user (England) has an army dislodged from Norway that must retreat or disband.",
    game: makeGame("active-retreat", "Northern Standoff", members, [
      spring,
      fallMove,
      retreat,
    ], {
      orderStatus: "orders_required",
      memberStatus: [],
    }),
    phases: [spring, fallMove, retreat],
    ordersByPhase: {
      202: [
        makeOrder({
          nationId: "england",
          unitType: "Army",
          orderType: "Move",
          source: "yor",
          target: "nwy",
          succeeded: false,
          failedBy: "stp",
        }),
        makeOrder({
          nationId: "england",
          unitType: "Fleet",
          orderType: "Move",
          source: "nth",
          target: "nwy",
          succeeded: false,
          failedBy: "stp",
        }),
        makeOrder({
          nationId: "england",
          unitType: "Fleet",
          orderType: "Hold",
          source: "nrg",
        }),
      ],
      203: [],
    },
    phaseStates: [
      makePhaseState(members[0], ["nwy"]),
      makePhaseState(members[1], []),
      makePhaseState(members[2], []),
      makePhaseState(members[3], []),
      makePhaseState(members[4], []),
      makePhaseState(members[5], []),
      makePhaseState(members[6], []),
    ],
    channels: [makeChannel("Public Press", members, [])],
  });
};

export const activeGameRetreat = buildActiveRetreat();

const buildActiveRetreatWindowClosed = () => {
  const members = makeActiveMembers();
  const springUnits = classicalStartUnits.map(u => {
    if (u.province.id === "lon") return makeUnit("Fleet", "england", "nth");
    if (u.province.id === "edi") return makeUnit("Fleet", "england", "nrg");
    if (u.province.id === "lvp") return makeUnit("Army", "england", "yor");
    if (u.province.id === "kie") return makeUnit("Fleet", "germany", "den");
    if (u.province.id === "ber") return makeUnit("Army", "germany", "kie");
    return u;
  });
  const fallUnits = springUnits.map(u => {
    if (u.province.id === "yor")
      return makeUnit("Army", "england", "nwy", {
        dislodged: true,
        dislodgedBy: { type: "Army", nation: "Russia", province: "nwy" },
      });
    if (u.province.id === "stp") return makeUnit("Army", "russia", "nwy");
    return u;
  });
  const spring = makePhase(211, 1, { status: "completed", nextPhaseId: 212 });
  const fallMove = makePhase(212, 2, {
    season: "Fall",
    status: "completed",
    units: springUnits,
    previousPhaseId: 211,
    nextPhaseId: 213,
  });
  const retreat = makePhase(213, 3, {
    season: "Fall",
    type: "Retreat",
    remainingTime: 10 * 60 * 60,
    units: fallUnits,
    previousPhaseId: 212,
    earlyResolveWindowEnd: futureIso(-3600),
  });
  return makeFixture({
    description:
      "Active game in a Fall 1901 retreat phase. Acceleration window has closed — confirm button is disabled.",
    game: makeGame("active-retreat-window-closed", "Northern Standoff II", members, [
      spring,
      fallMove,
      retreat,
    ], {
      orderStatus: "orders_required",
      memberStatus: [],
      deadlineMode: "fixed_time",
      acceleratedPhaseWindowSeconds: 14400,
    }),
    phases: [spring, fallMove, retreat],
    ordersByPhase: { 213: [] },
    phaseStates: [
      makePhaseState(members[0], ["nwy"]),
      makePhaseState(members[1], []),
      makePhaseState(members[2], []),
      makePhaseState(members[3], []),
      makePhaseState(members[4], []),
      makePhaseState(members[5], []),
      makePhaseState(members[6], []),
    ],
    channels: [makeChannel("Public Press", members, [])],
  });
};

export const activeGameRetreatWindowClosed = buildActiveRetreatWindowClosed();

const buildActiveBuild = () => {
  const members = makeActiveMembers();
  const fallUnits = classicalStartUnits.map(u => {
    if (u.province.id === "lon") return makeUnit("Fleet", "england", "nth");
    if (u.province.id === "edi") return makeUnit("Fleet", "england", "nwy");
    if (u.province.id === "lvp") return makeUnit("Army", "england", "yor");
    return u;
  });
  const supplyCenters = [
    ...classicalStartSupplyCenters,
    makeSupplyCenter("england", "nwy"),
  ];
  const spring = makePhase(301, 1, { status: "completed", nextPhaseId: 302 });
  const fallMove = makePhase(302, 2, {
    season: "Fall",
    status: "completed",
    units: fallUnits,
    previousPhaseId: 301,
    nextPhaseId: 303,
  });
  const adjustment = makePhase(303, 3, {
    season: "Fall",
    type: "Adjustment",
    remainingTime: 12 * 60 * 60,
    units: fallUnits,
    supplyCenters,
    previousPhaseId: 302,
  });
  return makeFixture({
    description:
      "Active game in a Fall 1901 build (adjustment) phase. The current user (England) captured Norway and can build one unit in a vacant home supply center.",
    game: makeGame("active-build", "Winter Council", members, [
      spring,
      fallMove,
      adjustment,
    ], {
      orderStatus: "orders_required",
      memberStatus: [],
    }),
    phases: [spring, fallMove, adjustment],
    ordersByPhase: {
      302: [
        makeOrder({
          nationId: "england",
          unitType: "Fleet",
          orderType: "Move",
          source: "edi",
          target: "nwy",
        }),
        makeOrder({
          nationId: "england",
          unitType: "Fleet",
          orderType: "Move",
          source: "lon",
          target: "nth",
        }),
        makeOrder({
          nationId: "england",
          unitType: "Army",
          orderType: "Move",
          source: "lvp",
          target: "yor",
        }),
      ],
      303: [],
    },
    phaseStates: [
      makePhaseState(members[0], ["lon", "edi", "lvp"]),
      makePhaseState(members[1], []),
      makePhaseState(members[2], []),
      makePhaseState(members[3], []),
      makePhaseState(members[4], []),
      makePhaseState(members[5], []),
      makePhaseState(members[6], []),
    ],
    channels: [makeChannel("Public Press", members, [])],
  });
};

export const activeGameBuild = buildActiveBuild();

const buildActiveDrawProposal = () => {
  const members = makeActiveMembers();
  const phase = makePhase(401, 3, {
    year: 1902,
    remainingTime: 30 * 60 * 60,
  });
  const proposal: DrawProposal = {
    id: 1,
    createdBy: {
      id: members[1].id,
      userId: members[1].userId,
      name: members[1].name,
      picture: null,
      isCurrentUser: false,
      nation: "Austria",
    },
    status: "pending",
    acceptedCount: 2,
    rejectedCount: 0,
    pendingCount: 5,
    totalVotes: 7,
    includedMemberIds: members.map(m => m.id),
    myVote: { included: true, accepted: null },
    phaseId: 401,
    createdAt: futureIso(-2 * 60 * 60),
  };
  return makeFixture({
    description:
      "Active game (Spring 1902 movement) with an open draw proposal created by Austria. The current user has not voted yet.",
    game: makeGame("active-draw-proposal", "Talk of Peace", members, [phase]),
    phases: [phase],
    ordersByPhase: { 401: [] },
    phaseStates: [
      makePhaseState(members[0], ["lon", "edi", "lvp"]),
      makePhaseState(members[1], ["vie", "bud", "tri"]),
      makePhaseState(members[2], ["par", "mar", "bre"]),
      makePhaseState(members[3], ["ber", "mun", "kie"]),
      makePhaseState(members[4], ["rom", "ven", "nap"]),
      makePhaseState(members[5], ["mos", "stp", "war", "sev"]),
      makePhaseState(members[6], ["con", "ank", "smy"]),
    ],
    channels: [makeChannel("Public Press", members, [])],
    drawProposals: [proposal],
  });
};

export const activeGameDrawProposal = buildActiveDrawProposal();

const buildFinishedSolo = () => {
  const members = makeActiveMembers().map(m =>
    m.nation === "Austria" || m.nation === "Italy"
      ? { ...m, eliminated: true }
      : m
  );
  const finalPhase = makePhase(501, 17, {
    season: "Fall",
    year: 1905,
    status: "completed",
    remainingTime: 0,
  });
  const game = makeGame("finished-solo", "March to Eighteen", members, [
    finalPhase,
  ]);
  return makeFixture({
    description:
      "Finished game won by the current user (England) with a solo victory. Austria and Italy were eliminated.",
    game: {
      ...game,
      status: "completed",
      victory: {
        id: 1,
        type: "solo",
        winningPhaseId: 501,
        members: [members[0]],
      },
    },
    phases: [finalPhase],
    ordersByPhase: { 501: [] },
    channels: [makeChannel("Public Press", members, [])],
  });
};

export const finishedGameSolo = buildFinishedSolo();

const buildFinishedDraw = () => {
  const members = makeActiveMembers();
  const finalPhase = makePhase(601, 21, {
    season: "Fall",
    year: 1906,
    status: "completed",
    remainingTime: 0,
  });
  const game = makeGame("finished-draw", "Stalemate Lines", members, [
    finalPhase,
  ]);
  return makeFixture({
    description:
      "Finished game that ended in a three-way draw between England (the current user), France, and Turkey.",
    game: {
      ...game,
      status: "completed",
      victory: {
        id: 2,
        type: "draw",
        winningPhaseId: 601,
        members: [members[0], members[2], members[6]],
      },
    },
    phases: [finalPhase],
    ordersByPhase: { 601: [] },
    channels: [makeChannel("Public Press", members, [])],
  });
};

export const finishedGameDraw = buildFinishedDraw();

const buildNotJoined = () => {
  const members = NATION_ASSIGNMENT.map(([playerIndex, nation], index) =>
    makeMember(players[playerIndex], nation, {
      isCurrentUser: false,
      userId: 100 + index,
      isGameCreator: index === 0,
    })
  );
  const phase = makePhase(701, 1, { remainingTime: 40 * 60 * 60 });
  return makeFixture({
    description:
      "Active public game that the current user is not a member of (spectator view). No orders or phase state for the current user.",
    game: makeGame("not-joined", "Spectator Derby", members, [phase]),
    phases: [phase],
    ordersByPhase: { 701: [] },
    phaseStates: members.map(m => makePhaseState(m, [])),
    channels: [makeChannel("Public Press", members, [])],
  });
};

export const gameNotJoined = buildNotJoined();
