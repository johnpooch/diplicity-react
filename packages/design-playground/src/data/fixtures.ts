import type { Channel, Game, Member, Profile } from "./types";

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
