import type {
  BlockedReasonEnum,
  GameAction,
  Member,
  MemberAction,
  MemberDetail,
  ParticipationStatusEnum,
} from "@/api/generated/endpoints";
import { currentUserProfile, nation, type GameFixture } from "./fixtures";

const action = <K extends string>(
  key: K,
  blockedReason: BlockedReasonEnum | null = null
) => ({ key, blockedReason });

const removeBlocked = action("remove_from_game", "no_missed_orders");

const each = (keys: string[], actions: MemberAction[]) =>
  Object.fromEntries(keys.map(key => [key, actions]));

export const GAME_MASTER_MEMBER_IDS: Record<string, number> = {
  "game-master": 9001,
  "active-game-master-chat": 9002,
  "game-master-mustering": 9003,
};

const MEMBER_ACTIONS: Record<string, Record<string, MemberAction[]>> = {
  "pending-some-players": each(
    ["Alice", "Bob", "The Dealmaker"],
    [action("remove_from_lobby")]
  ),
  "pending-almost-full": each(
    ["Alice", "Bob", "Charlie", "Diana", "Eve"],
    [action("remove_from_lobby")]
  ),
  "game-master": each(
    ["England", "Bob", "Charlie"],
    [action("remove_from_lobby")]
  ),
  "game-master-mustering": each(
    ["Alice", "Bob", "Charlie", "Diana", "Eve", "Frank", "Grace"],
    [action("remove_from_lobby")]
  ),
  "active-game-master-chat": each(
    ["England", "Austria", "France", "Germany", "Italy", "Russia", "Turkey"],
    [removeBlocked]
  ),
  "active-seat-open": {
    ...each(["Austria", "France", "Germany", "Russia"], [removeBlocked]),
    Italy: [action("remove_from_game")],
    Turkey: [action("share_replacement_link")],
  },
  "seat-open-spectator": {
    Turkey: [action("take_over"), action("share_replacement_link")],
  },
  "seat-open-locked": {
    Turkey: [
      action("take_over", "commitment_too_low"),
      action("share_replacement_link"),
    ],
  },
  "active-withdrawn-player": {
    France: [action("share_replacement_link")],
  },
};

const PARTICIPATION: Record<string, Record<string, ParticipationStatusEnum>> = {
  "mustering-game": {
    Alice: "seat_confirmed",
    Bob: "seat_confirmed",
    Charlie: "seat_confirmed",
  },
  "mustering-confirmed": {
    "Mock Player": "seat_confirmed",
    Alice: "seat_confirmed",
  },
};

const REPLACED_MEMBERS: Record<string, MemberDetail> = {
  "active-seat-open": {
    id: 1199,
    userId: 8,
    name: "Grace",
    picture: null,
    isCurrentUser: false,
    isBot: false,
    commitment: "low",
    isAdmin: false,
    nation: "Turkey",
    participationStatus: "replaced",
    supplyCenterCount: null,
    unitCount: null,
    nmrExtensionsRemaining: 0,
    nmrExtensionsAllowed: 2,
    nationPreferences: null,
    actions: [],
  },
};

const GAME_INFO_KEYS: GameAction["key"][] = [
  "join",
  "confirm_seat",
  "extend_deadline",
  "pause",
  "unpause",
  "clone_to_sandbox",
  "leave",
  "withdraw",
  "delete",
];

const PLAYER_LIST_KEYS: GameAction["key"][] = [
  "edit_nation_preferences",
  "assign_nations",
];

const SEAT_KEYS: GameAction["key"][] = ["confirm_seat", "leave", "withdraw"];

const availableGameActions = ({ game }: GameFixture) => {
  const isPlayer = game.members.some(member => member.isCurrentUser);
  const isGameMaster = game.gameMaster?.userId === currentUserProfile.userId;
  const active = game.status === "active";
  const manages = game.canManage && active;
  return new Set<GameAction["key"]>(
    (
      [
        ["join", game.canJoin],
        ["confirm_seat", game.musterStatus === "confirmation_required"],
        ["edit_nation_preferences", game.status === "pending" && isPlayer],
        ["assign_nations", game.status === "pending" && isGameMaster],
        ["extend_deadline", manages && !game.isPaused],
        ["pause", manages && !game.isPaused],
        ["unpause", manages && game.isPaused],
        ["clone_to_sandbox", active && !game.sandbox && isPlayer],
        ["leave", game.canLeave],
        ["withdraw", game.canWithdraw],
        ["delete", game.canDelete],
      ] as [GameAction["key"], boolean][]
    )
      .filter(([, available]) => available)
      .map(([key]) => key)
  );
};

const actionsFrom = (fixture: GameFixture, keys: GameAction["key"][]) => {
  const available = availableGameActions(fixture);
  return keys.filter(key => available.has(key)).map(key => action(key));
};

export const gameActionsFor = (fixture: GameFixture): GameAction[] =>
  actionsFrom(fixture, GAME_INFO_KEYS);

export const playerListActionsFor = (fixture: GameFixture): GameAction[] =>
  actionsFrom(fixture, PLAYER_LIST_KEYS);

const defaultStatus = (
  { game }: GameFixture,
  member: Member
): ParticipationStatusEnum => {
  const victors = game.victory?.members.map(victor => victor.id) ?? [];
  if (member.kicked) return "removed";
  if (member.withdrawn) return "withdrawn";
  if (victors.includes(member.id)) return victors.length === 1 ? "won" : "drew";
  if (member.eliminated) return "eliminated";
  if (member.civilDisorder) return "civil_disorder";
  if (game.status === "mustering") {
    if (member.isBot) return "seat_confirmed";
    if (member.isCurrentUser && game.musterStatus === "confirmed")
      return "seat_confirmed";
    return "seat_unconfirmed";
  }
  if (game.status === "pending") return "joined";
  return "playing";
};

const gameMasterDetail = (fixture: GameFixture, id: number): MemberDetail => ({
  id,
  userId: fixture.game.gameMaster?.userId ?? null,
  name: fixture.game.gameMaster?.name ?? "",
  picture: fixture.game.gameMaster?.picture ?? null,
  isCurrentUser: fixture.game.gameMaster?.userId === currentUserProfile.userId,
  isBot: false,
  commitment: null,
  isAdmin: true,
  nation: null,
  participationStatus: "game_master",
  supplyCenterCount: null,
  unitCount: null,
  nmrExtensionsRemaining: 0,
  nmrExtensionsAllowed: fixture.game.nmrExtensionsAllowed,
  nationPreferences: null,
  actions: actionsFrom(fixture, SEAT_KEYS),
});

export const memberDetailFor = (
  fixture: GameFixture,
  memberId: number
): MemberDetail | null => {
  const { game } = fixture;
  if (GAME_MASTER_MEMBER_IDS[game.id] === memberId) {
    return gameMasterDetail(fixture, memberId);
  }
  if (REPLACED_MEMBERS[game.id]?.id === memberId) {
    return REPLACED_MEMBERS[game.id];
  }
  const member = game.members.find(candidate => candidate.id === memberId);
  if (!member) return null;

  const key = member.nation ?? member.name;
  const started = game.status !== "pending" && game.status !== "mustering";
  const phase = fixture.phases[fixture.phases.length - 1];
  const countFor = (items: readonly { nation: { name: string } }[]) =>
    started && phase && member.nation
      ? items.filter(item => item.nation.name === member.nation).length
      : null;

  return {
    id: member.id,
    userId: member.userId,
    name: member.name,
    picture: member.picture,
    isCurrentUser: member.isCurrentUser,
    isBot: member.isBot,
    commitment: member.commitment,
    isAdmin: member.isAdmin,
    nation: member.nation,
    participationStatus:
      PARTICIPATION[game.id]?.[key] ?? defaultStatus(fixture, member),
    supplyCenterCount: countFor(phase?.supplyCenters ?? []),
    unitCount: countFor(phase?.units ?? []),
    nmrExtensionsRemaining: member.nmrExtensionsRemaining,
    nmrExtensionsAllowed: game.nmrExtensionsAllowed,
    nationPreferences:
      member.isCurrentUser && game.status === "pending"
        ? member.nationPreferenceIds.map(nationId => nation(nationId).name)
        : null,
    actions: member.isCurrentUser
      ? actionsFrom(fixture, SEAT_KEYS)
      : (MEMBER_ACTIONS[game.id]?.[key] ?? []),
  };
};
