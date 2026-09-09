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

export type PlayerRole = "admin" | "bot";

export type PlayerCardPresentation = "identity" | "nation";

export interface Player {
  id: string;
  name: string;
  picture?: string;
  role?: PlayerRole;
  isCurrentUser?: boolean;
  preferredNation?: string;
  assignedNation?: string;
  status?: string;
  supplyCenterCount?: number;
  unitCount?: number;
  eliminated?: boolean;
  anonymous?: boolean;
  gameMaster?: boolean;
}

export interface Phase {
  season: string;
  year: number;
  type: PhaseType;
  deadline: string;
}

export interface Variant {
  id: string;
  name: string;
  description: string;
  victoryConditions: string;
}

export type GameInfoSettingIcon =
  | "calendar"
  | "lock"
  | "shield-plus"
  | "message-circle-off";

export interface GameInfoSetting {
  label: string;
  value?: string;
  info?: string;
  icon?: GameInfoSettingIcon;
}

export interface GameInfo {
  name: string;
  variant: Variant;
  phaseDeadlines: GameInfoSetting[];
  settings: GameInfoSetting[];
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

export interface ChannelPreview {
  id: string;
  name: string;
  nations: string[];
  lastSender?: string;
  lastBody?: string;
  unread?: boolean;
}

export interface ChatMessage {
  id: string;
  type: "message";
  sender: string;
  nation: string;
  body: string;
  sentAt: string;
  isCurrentUser: boolean;
}

export interface ChatPhase {
  id: string;
  type: "phase";
  label: string;
}

export type ChatEntry = ChatMessage | ChatPhase;

export interface ChatThread {
  id: string;
  name: string;
  subtitle: string;
  kind: "direct" | "group";
  entries: ChatEntry[];
}

export type UnitType = "Army" | "Fleet";

export type OrderKind =
  | "move"
  | "hold"
  | "support"
  | "convoy"
  | "retreat"
  | "disband"
  | "build";

export interface OrderSlot {
  id: string;
  province: string;
  unitType?: UnitType;
  kind?: OrderKind;
  summary?: string;
}

export interface CurrentPhaseOrders {
  phaseName: string;
  timeRemaining: string;
  nation: string;
  supplyCenterCount: number;
  unitCount: number;
  slots: OrderSlot[];
  confirmed: boolean;
  sandbox?: boolean;
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
