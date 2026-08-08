export type GameStatus = "pending" | "active" | "completed";

export type PhaseType = "Movement" | "Retreat" | "Adjustment";

export type OrderStatus =
  | "orders_required"
  | "orders_submitted"
  | "orders_confirmed"
  | "no_orders_required";

export interface Member {
  nation: string;
  username: string;
  isBot: boolean;
  isCurrentUser: boolean;
}

export interface Phase {
  season: string;
  year: number;
  type: PhaseType;
  deadline: string;
}

export interface Game {
  id: string;
  name: string;
  status: GameStatus;
  variant: string;
  phase: Phase;
  members: Member[];
  playerCount: number;
  orderStatus: OrderStatus;
  unreadCount: number;
  isPrivate: boolean;
  winner?: string;
}

export interface Message {
  id: string;
  sender: string;
  nation: string;
  body: string;
  sentAt: string;
  isCurrentUser: boolean;
}

export interface Channel {
  id: string;
  name: string;
  members: string[];
  messages: Message[];
}

export interface ProfileStat {
  label: string;
  value: string;
  hint?: string;
}

export interface Profile {
  username: string;
  joinedAt: string;
  bio: string;
  stats: ProfileStat[];
  favouriteNation: string;
  recentResults: Array<{
    gameName: string;
    nation: string;
    outcome: "Won" | "Drew" | "Eliminated" | "Resigned";
    finishedAt: string;
  }>;
}
