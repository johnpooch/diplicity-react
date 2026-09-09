import type {
  Channel,
  ChannelPreview,
  ChatMessage,
  ChatThread,
  CurrentPhaseOrders,
  Game,
  GameInfo,
  Member,
  Player,
  Profile,
  Variant,
} from "./types";

export const sengokuVariant: Variant = {
  id: "sengoku",
  name: "Sengoku",
  description:
    "Battle it out during the Sengoku (warring states) period of 16th Century Japan which collapsed the feudal system under the Ashikaga Shogunate. Select one of seven clans to become the new Shogun.",
  victoryConditions: "Control 18 supply centers",
};

export const classicalVariant: Variant = {
  id: "classical",
  name: "Classical",
  description: "The original Diplomacy.",
  victoryConditions: "The first to 18 Supply Centers (SC) is the winner.",
};

export const unconstitutionalVariant: Variant = {
  id: "unconstitutional",
  name: "Unconstitutional",
  description:
    "Alternative history variant where the US constitution was not ratified (which nearly happened). Operating under the weak Articles of Confederation, States keep their conflicting land claims and border disputes turn into armed conflict. Former slaves control Haiti, and inhabitants of New Orleans, Saint Louis and the Turks and Cacois oppose annexation by the US. Federal government ceases to function, many States have seceded and two groups of Native American tribes, the Western and Muskogee Confederacy, are warning the Americans.",
  victoryConditions:
    "First to 18 supply centers, or the most centers when the year 1810 is reached.",
};

export const variants: Variant[] = [
  sengokuVariant,
  classicalVariant,
  unconstitutionalVariant,
];

export const brushOfFramePending: GameInfo = {
  name: "The Brush of Frame",
  variant: classicalVariant,
  phaseDeadlines: [
    { label: "Movement", value: "24 hours" },
    { label: "Retreat/Adjustment", value: "12 hours" },
    {
      label: "Deadline extensions",
      value: "1 per player",
      info: "If a player does not submit orders on time a deadline extension is used.",
    },
  ],
  settings: [{ label: "Created", value: "12 March 2026", icon: "calendar" }],
};

export const brushOfFramePendingNoExtensions: GameInfo = {
  ...brushOfFramePending,
  phaseDeadlines: brushOfFramePending.phaseDeadlines.filter(
    row => row.label !== "Deadline extensions"
  ),
};

export const brushOfFramePrivate: GameInfo = {
  ...brushOfFramePending,
  settings: [
    ...brushOfFramePending.settings,
    { label: "Private", icon: "lock" },
  ],
};

export const brushOfFrameHighCommitment: GameInfo = {
  ...brushOfFramePending,
  settings: [
    ...brushOfFramePending.settings,
    { label: "High commitment players", icon: "shield-plus" },
  ],
};

export const brushOfFrameGunboat: GameInfo = {
  ...brushOfFramePending,
  settings: [
    ...brushOfFramePending.settings,
    {
      label: "Gunboat",
      icon: "message-circle-off",
      info: "Player names are hidden and chat is disabled.",
    },
  ],
};

export const brushOfFramePrivateGunboat: GameInfo = {
  ...brushOfFramePending,
  settings: [
    ...brushOfFramePending.settings,
    { label: "Private", icon: "lock" },
    {
      label: "Gunboat",
      icon: "message-circle-off",
      info: "Player names are hidden and chat is disabled.",
    },
  ],
};

export const nations = [
  "Austria",
  "England",
  "France",
  "Germany",
  "Italy",
  "Russia",
  "Turkey",
];

const member = (
  nation: string,
  username: string,
  overrides: Partial<Member> = {}
): Member => ({
  nation,
  username,
  isBot: false,
  isCurrentUser: false,
  ...overrides,
});

const fullTable: Member[] = [
  member("Austria", "otto", { isCurrentUser: true }),
  member("England", "wilhelmina"),
  member("France", "dealmakerbot", { isBot: true }),
  member("Germany", "kaiserbill"),
  member("Italy", "garibaldi"),
  member("Russia", "tsarina"),
  member("Turkey", "sublimeporte"),
];

export const activeGame: Game = {
  id: "1",
  name: "The Congress of Vienna",
  status: "active",
  variant: "Classical",
  phase: {
    season: "Spring",
    year: 1903,
    type: "Movement",
    deadline: "in 14 hours",
  },
  members: fullTable,
  playerCount: 7,
  orderStatus: "orders_required",
  unreadCount: 3,
  isPrivate: false,
};

export const activeGameSubmitted: Game = {
  ...activeGame,
  id: "2",
  name: "Hundred Years",
  phase: { ...activeGame.phase, year: 1908, deadline: "in 2 days" },
  orderStatus: "orders_submitted",
  unreadCount: 0,
};

export const activeGameRetreat: Game = {
  ...activeGame,
  id: "3",
  name: "Winter Offensive",
  phase: {
    season: "Autumn",
    year: 1905,
    type: "Retreat",
    deadline: "in 40 minutes",
  },
  orderStatus: "no_orders_required",
  unreadCount: 12,
};

export const activeGameBuild: Game = {
  ...activeGame,
  id: "4",
  name: "Diplomacy Club Ladder",
  phase: {
    season: "Winter",
    year: 1904,
    type: "Adjustment",
    deadline: "in 6 hours",
  },
  orderStatus: "orders_confirmed",
  unreadCount: 0,
  isPrivate: true,
};

export const pendingGame: Game = {
  id: "5",
  name: "Sunday Night Gunboat",
  status: "pending",
  variant: "Classical",
  phase: { season: "Spring", year: 1901, type: "Movement", deadline: "—" },
  members: fullTable.slice(0, 4),
  playerCount: 7,
  orderStatus: "no_orders_required",
  unreadCount: 0,
  isPrivate: false,
};

export const pendingGameAlmostFull: Game = {
  ...pendingGame,
  id: "6",
  name: "Bots & Humans",
  members: fullTable.slice(0, 6),
};

export const completedGame: Game = {
  ...activeGame,
  id: "7",
  name: "The Long Game",
  status: "completed",
  phase: {
    season: "Autumn",
    year: 1917,
    type: "Movement",
    deadline: "finished",
  },
  orderStatus: "no_orders_required",
  unreadCount: 0,
  winner: "Austria",
};

export const games: Game[] = [
  activeGame,
  activeGameRetreat,
  activeGameSubmitted,
  activeGameBuild,
  pendingGame,
  pendingGameAlmostFull,
  completedGame,
];

export const manyGames: Game[] = [
  ...games,
  ...games.map((game, index) => ({
    ...game,
    id: `${game.id}-b`,
    name: `${game.name} II`,
    unreadCount: index % 3 === 0 ? index : 0,
  })),
];

export const channel: Channel = {
  id: "1",
  name: "Austria, England, Russia",
  members: ["Austria", "England", "Russia"],
  messages: [
    {
      id: "1",
      sender: "wilhelmina",
      nation: "England",
      body: "I'm not moving to the North Sea this year. You have my word.",
      sentAt: "09:12",
      isCurrentUser: false,
    },
    {
      id: "2",
      sender: "tsarina",
      nation: "Russia",
      body: "That is exactly what someone moving to the North Sea would say.",
      sentAt: "09:14",
      isCurrentUser: false,
    },
    {
      id: "3",
      sender: "otto",
      nation: "Austria",
      body: "Can we agree a DMZ in Galicia for two years? I'd rather look south.",
      sentAt: "09:20",
      isCurrentUser: true,
    },
    {
      id: "4",
      sender: "tsarina",
      nation: "Russia",
      body: "Two years is a long time. One, and I'll support you into Greece in the autumn.",
      sentAt: "09:31",
      isCurrentUser: false,
    },
    {
      id: "5",
      sender: "otto",
      nation: "Austria",
      body: "Deal. Galicia stays empty through 1904.",
      sentAt: "09:33",
      isCurrentUser: true,
    },
  ],
};

export const emptyChannel: Channel = {
  ...channel,
  messages: [],
};

export const activeChannelList: ChannelPreview[] = [
  {
    id: "public",
    name: "Public Press",
    nations: [],
    lastSender: "France",
    lastBody:
      "May the best player win! I've posted my opening in the Channel and I hope we can all keep this civil through 1901 at least.",
  },
  {
    id: "france",
    name: "France",
    nations: ["France"],
    lastSender: "You",
    lastBody: "Agreed, I'll attack Belgium",
    unread: true,
  },
  {
    id: "alliance",
    name: "The great alliance",
    nations: ["Austria", "France"],
    lastSender: "Austria",
    lastBody: "I'm in ;)",
  },
];

export const pendingChannelList: ChannelPreview[] = [
  {
    id: "public",
    name: "Public Press",
    nations: [],
    lastSender: "Jane Doe",
    lastBody:
      "Looking forward to this one. I've played Classical a dozen times and I'm hoping we get a full table before the weekend.",
  },
];

export const johnDoe: Player = {
  id: "john-doe",
  name: "John Doe",
  picture: "/otto.png",
  role: "admin",
  isCurrentUser: true,
  preferredNation: "Austria",
};

export const zaraGameMaster: Player = {
  id: "zara",
  name: "Zara",
  gameMaster: true,
};

export const johnDoeNoPreferences: Player = {
  ...johnDoe,
  preferredNation: undefined,
};

export const janeDoe: Player = {
  id: "jane-doe",
  name: "Jane Doe",
  assignedNation: "France",
};

export const theChancellor: Player = {
  id: "the-chancellor",
  name: "The chancellor",
  role: "bot",
};

export const wilhelmina: Player = {
  id: "wilhelmina",
  name: "Wilhelmina",
  preferredNation: "England",
};

export const johnDoeMustering: Player = {
  ...johnDoe,
  status: "Confirmed",
};

export const janeDoeMustering: Player = {
  ...janeDoe,
  status: "Not confirmed",
};

export const theChancellorMustering: Player = {
  ...theChancellor,
  status: "Confirmed",
};

export const johnDoeActive: Player = {
  ...johnDoe,
  preferredNation: undefined,
  assignedNation: "France",
  supplyCenterCount: 3,
  unitCount: 3,
};

export const janeDoeActive: Player = {
  ...janeDoe,
  assignedNation: "Germany",
  supplyCenterCount: 3,
  unitCount: 4,
};

export const theChancellorActive: Player = {
  ...theChancellor,
  assignedNation: "England",
  supplyCenterCount: 3,
  unitCount: 2,
};

export const ottoActive: Player = {
  id: "otto",
  name: "Otto",
  assignedNation: "Austria",
  supplyCenterCount: 5,
  unitCount: 5,
};

export const giuseppeActive: Player = {
  id: "giuseppe",
  name: "Giuseppe",
  assignedNation: "Italy",
  supplyCenterCount: 3,
  unitCount: 3,
};

export const tsarinaActive: Player = {
  id: "tsarina",
  name: "Tsarina",
  assignedNation: "Russia",
  supplyCenterCount: 4,
  unitCount: 4,
};

export const sultanActive: Player = {
  id: "sultan",
  name: "Sultan",
  assignedNation: "Turkey",
  supplyCenterCount: 3,
  unitCount: 3,
};

export const createChannelMembers: Player[] = [
  ottoActive,
  janeDoeActive,
  theChancellorActive,
  giuseppeActive,
  tsarinaActive,
  sultanActive,
];

export const johnDoeAnon: Player = {
  ...johnDoeActive,
  anonymous: true,
};

export const janeDoeAnon: Player = {
  ...janeDoeActive,
  anonymous: true,
};

export const johnDoeSolo: Player = {
  ...johnDoeActive,
  supplyCenterCount: 18,
  unitCount: 18,
};

export const janeDoeEliminated: Player = {
  ...janeDoeActive,
  supplyCenterCount: 0,
  unitCount: 0,
  eliminated: true,
};

export const theChancellorEliminated: Player = {
  ...theChancellorActive,
  supplyCenterCount: 0,
  unitCount: 0,
  eliminated: true,
};

export const wilhelminaEliminated: Player = {
  ...wilhelmina,
  preferredNation: undefined,
  assignedNation: "Italy",
  supplyCenterCount: 0,
  unitCount: 0,
  eliminated: true,
};

export const wilhelminaFormer: Player = {
  ...wilhelmina,
  preferredNation: undefined,
  assignedNation: "France",
};

export const johnDoeDraw: Player = {
  ...johnDoeActive,
  supplyCenterCount: 9,
  unitCount: 9,
};

export const janeDoeDraw: Player = {
  ...janeDoeActive,
  supplyCenterCount: 9,
  unitCount: 9,
};

export const austriaMovementIncomplete: CurrentPhaseOrders = {
  phaseName: "Spring 1902, Movement",
  timeRemaining: "6 hours remaining",
  nation: "Austria",
  supplyCenterCount: 5,
  unitCount: 5,
  slots: [
    {
      id: "vie",
      unitType: "Army",
      province: "Vienna",
      kind: "move",
      summary: "Move to Galicia",
    },
    {
      id: "bud",
      unitType: "Army",
      province: "Budapest",
    },
    {
      id: "tri",
      unitType: "Fleet",
      province: "Trieste",
      kind: "hold",
      summary: "Hold",
    },
    {
      id: "alb",
      unitType: "Fleet",
      province: "Albania",
      kind: "convoy",
      summary: "Convoy Army Serbia to Greece",
    },
    {
      id: "ser",
      unitType: "Army",
      province: "Serbia",
      kind: "support",
      summary: "Support Army Vienna to Galicia",
    },
  ],
  confirmed: false,
};

export const austriaMovementConfirmed: CurrentPhaseOrders = {
  ...austriaMovementIncomplete,
  slots: austriaMovementIncomplete.slots.map(slot =>
    slot.id === "bud"
      ? {
          ...slot,
          kind: "support",
          summary: "Support Army Vienna to Galicia",
        }
      : slot
  ),
  confirmed: true,
};

export const austriaRetreat: CurrentPhaseOrders = {
  phaseName: "Autumn 1902, Retreat",
  timeRemaining: "40 minutes remaining",
  nation: "Austria",
  supplyCenterCount: 4,
  unitCount: 4,
  slots: [
    {
      id: "mun",
      unitType: "Army",
      province: "Munich",
      kind: "retreat",
      summary: "Retreat to Bohemia",
    },
    {
      id: "tyr",
      unitType: "Army",
      province: "Tyrolia",
      kind: "disband",
      summary: "Disband",
    },
  ],
  confirmed: false,
};

export const austriaAdjustment: CurrentPhaseOrders = {
  phaseName: "Winter 1902, Adjustment",
  timeRemaining: "11 hours remaining",
  nation: "Austria",
  supplyCenterCount: 5,
  unitCount: 3,
  slots: [
    {
      id: "bud-build",
      province: "Budapest",
      kind: "build",
      summary: "Build army",
    },
    {
      id: "vie-build",
      province: "Vienna",
    },
  ],
  confirmed: false,
};

export const austriaRetreatConfirmed: CurrentPhaseOrders = {
  ...austriaRetreat,
  confirmed: true,
};

export const austriaAdjustmentConfirmed: CurrentPhaseOrders = {
  ...austriaAdjustment,
  slots: [
    austriaAdjustment.slots[0],
    {
      id: "vie-build",
      province: "Vienna",
      kind: "build",
      summary: "Build fleet",
    },
  ],
  confirmed: true,
};

export const austriaNoRetreats: CurrentPhaseOrders = {
  phaseName: "Autumn 1902, Retreat",
  timeRemaining: "40 minutes remaining",
  nation: "Austria",
  supplyCenterCount: 5,
  unitCount: 5,
  slots: [],
  confirmed: false,
};

export const austriaNoAdjustments: CurrentPhaseOrders = {
  phaseName: "Winter 1902, Adjustment",
  timeRemaining: "11 hours remaining",
  nation: "Austria",
  supplyCenterCount: 5,
  unitCount: 5,
  slots: [],
  confirmed: false,
};

export const austriaNoMovement: CurrentPhaseOrders = {
  phaseName: "Spring 1902, Movement",
  timeRemaining: "6 hours remaining",
  nation: "Austria",
  supplyCenterCount: 5,
  unitCount: 5,
  slots: [],
  confirmed: false,
};

export const austriaSandbox: CurrentPhaseOrders = {
  ...austriaMovementIncomplete,
  sandbox: true,
};

export const profile: Profile = {
  username: "otto",
  joinedAt: "March 2021",
  bio: "Mostly Austria. Occasionally regrets it.",
  favouriteNation: "Austria",
  stats: [
    { label: "Games played", value: "48" },
    { label: "Solo victories", value: "6", hint: "12.5% of games" },
    { label: "Draws", value: "19" },
    { label: "Reliability", value: "97%", hint: "3 missed deadlines" },
  ],
  recentResults: [
    {
      gameName: "The Long Game",
      nation: "Austria",
      outcome: "Won",
      finishedAt: "2 weeks ago",
    },
    {
      gameName: "Sunday Night Gunboat",
      nation: "Turkey",
      outcome: "Drew",
      finishedAt: "1 month ago",
    },
    {
      gameName: "Diplomacy Club Ladder",
      nation: "Italy",
      outcome: "Eliminated",
      finishedAt: "2 months ago",
    },
  ],
};

const say = (
  id: string,
  nation: string,
  body: string,
  sentAt: string,
  isCurrentUser = false
): ChatMessage => ({
  id,
  type: "message",
  sender: isCurrentUser ? "otto" : nation.toLowerCase(),
  nation,
  body,
  sentAt,
  isCurrentUser,
});

const franceDirect = {
  id: "france",
  name: "France",
  subtitle: "Jane Doe",
  kind: "direct" as const,
};

const greatAlliance = {
  id: "alliance",
  name: "The great alliance",
  subtitle: "France, England",
  kind: "group" as const,
};

export const franceDirectEmpty: ChatThread = {
  ...franceDirect,
  entries: [{ id: "phase-1", type: "phase", label: "Spring 1901, Movement" }],
};

export const franceDirectOne: ChatThread = {
  ...franceDirect,
  entries: [
    { id: "phase-1", type: "phase", label: "Spring 1901, Movement" },
    say("1", "France", "Shall we bounce in the Channel?", "10:14"),
  ],
};

export const franceDirectMany: ChatThread = {
  ...franceDirect,
  entries: [
    { id: "phase-1", type: "phase", label: "Spring 1901, Movement" },
    say("1", "France", "Hi.", "09:02"),
    say(
      "2",
      "Austria",
      "Hi. I want Belgium. I'll stay out of Burgundy if you stay out of Munich.",
      "09:05",
      true
    ),
    say("3", "France", "Ok.", "09:06"),
    say(
      "4",
      "France",
      "Belgium is yours if you support me into the Channel in the autumn. England is lining up a convoy through the North Sea and I cannot hold Brest and Picardy if that fleet arrives on the coast.",
      "09:11"
    ),
    say("5", "Austria", "That's a long way from Vienna.", "09:13", true),
    say("6", "France", "I know.", "09:14"),
    say(
      "7",
      "Austria",
      "Agreed, I'll attack Belgium. You take the Channel. If England still goes south I can offer Munich the year after, not this one.",
      "09:22",
      true
    ),
    say("8", "France", "Deal.", "09:23"),
    { id: "phase-2", type: "phase", label: "Autumn 1901, Movement" },
    say("9", "France", "English fleet is in the North Sea.", "11:40"),
    say("10", "Austria", "Saw it.", "11:41", true),
    say(
      "11",
      "France",
      "Then we have to bounce him in the Channel this turn or I lose Brest. Army Picardy holds, fleet Brest to the Channel, you move to Belgium. If I misorder this we both look like fools.",
      "11:44"
    ),
    say("12", "Austria", "I'm in :)", "11:46", true),
    say("13", "France", "Thanks.", "11:47"),
    say("14", "France", "Good luck.", "11:48"),
  ],
};

export const greatAllianceOne: ChatThread = {
  ...greatAlliance,
  entries: [
    { id: "phase-1", type: "phase", label: "Spring 1901, Movement" },
    say("1", "France", "Let's work together against Germany!", "11:02"),
  ],
};

export const greatAllianceMany: ChatThread = {
  ...greatAlliance,
  entries: [
    { id: "phase-0", type: "phase", label: "Spring 1901, Movement" },
    say("1", "France", "Hi.", "08:12"),
    say("2", "England", "Hello.", "08:14"),
    say(
      "3",
      "France",
      "Let's work together against Germany. He opened to Ruhr and the North Sea. If we leave him alone he is in Belgium and Holland before winter.",
      "08:21"
    ),
    say("4", "England", "Agreed.", "08:22"),
    say(
      "5",
      "Austria",
      "I can pressure Munich from Tyrolia if you two take Belgium and Holland. I will not bounce you in the Channel.",
      "08:30",
      true
    ),
    say("6", "France", "Sounds good!", "08:31"),
    say("7", "England", "Ok.", "08:32"),
    say("8", "Austria", "I'm in :)", "08:33", true),
    { id: "phase-1", type: "phase", label: "Autumn 1901, Movement" },
    say("9", "France", "He went to Burgundy.", "10:02"),
    say("10", "England", "North Sea held.", "10:03"),
    say(
      "11",
      "England",
      "I can convoy to Belgium in the autumn if France covers Burgundy and Austria still walks to Munich. If either of you flinch I am landing on an empty coast with no support.",
      "10:11"
    ),
    say("12", "France", "I'll cover Burgundy.", "10:12"),
    say("13", "Austria", "Munich.", "10:13", true),
    say("14", "England", "Thanks.", "10:14"),
    { id: "phase-2", type: "phase", label: "Spring 1902, Movement" },
    say(
      "15",
      "France",
      "Germany supported himself to Belgium. Holland is open. We should talk about who takes it before we all bounce.",
      "14:08"
    ),
    say("16", "England", "Holland is mine.", "14:09"),
    say("17", "France", "Fine.", "14:10"),
    say(
      "18",
      "Austria",
      "Munich held. I can try again in the spring but I need someone to cut support from Ruhr or this is a waste of an army.",
      "14:18",
      true
    ),
    say("19", "France", "I'll cut Ruhr.", "14:19"),
    say("20", "England", "Deal.", "14:20"),
  ],
};
