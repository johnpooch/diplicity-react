export type GameStatus =
  | "pending"
  | "mustering"
  | "active"
  | "completed"
  | "abandoned";

export type PhaseType = "Movement" | "Retreat" | "Adjustment";

export type OrderStatus =
  | "orders_required"
  | "orders_submitted"
  | "orders_confirmed"
  | "no_orders_required";

export type GameAttention =
  | "confirm_seat"
  | "orders_required"
  | "orders_unconfirmed"
  | "missed_deadline"
  | "unread_messages"
  | "none";

export type MusteringStatus = "unconfirmed" | "confirmed";

export type GameResult = "solo_win" | "solo_loss" | "draw" | "abandoned";

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

export type ParticipationStatus =
  | "Playing"
  | "Seeking replacement"
  | "Civil disorder"
  | "Replaced"
  | "Removed"
  | "Eliminated";

export interface MemberDetails {
  player: Player;
  gameStatus: GameStatus;
  participationStatus: ParticipationStatus;
  nation?: string;
  supplyCenterCount?: number;
  unitCount?: number;
  result?: "Solo winner" | "Draw" | "Eliminated";
  deadlineExtensionsAllowed: number;
  deadlineExtensionsRemaining: number;
  nationPreferences?: string[];
  profilePath?: string;
  canEditPreferences?: boolean;
  canAssignNation?: boolean;
  canLeave?: boolean;
  canRequestReplacement?: boolean;
  canCancelReplacement?: boolean;
  canRecover?: boolean;
  canInviteReplacement?: boolean;
  canTakeOver?: boolean;
  removeControl?: {
    enabled: boolean;
    reason?: string;
  };
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
  "calendar" | "lock" | "shield-plus" | "message-circle-off";

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
  attention?: GameAttention;
  nation?: string;
  preferredNations?: string[];
  musteringStatus?: MusteringStatus;
  confirmedPlayers?: number;
  result?: GameResult;
  isGameMaster?: boolean;
  isPaused?: boolean;
  sandbox?: boolean;
  userInCivilDisorder?: boolean;
  otherPlayerInCivilDisorder?: boolean;
  userEliminated?: boolean;
  replaceableSeat?: boolean;
  urgencyRank?: number;
  deadlineMinutes?: number;
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
  "move" | "hold" | "support" | "convoy" | "retreat" | "disband" | "build";

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

export interface PhaseHistoryEntry {
  id: string;
  resolved: boolean;
  orders: CurrentPhaseOrders;
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

export type MyGamesSectionKey =
  | "needs_attention"
  | "managing"
  | "mustering"
  | "active"
  | "pending"
  | "recently_finished"
  | "sandbox";

export type MyGameDeparture = "eliminated" | "civil_disorder";

export type MyGameResult = "solo_victory" | "won_by" | "draw" | "abandoned" | "ongoing";

export type MyGameState =
  | {
      kind:
        | "confirm_seat"
        | "submit_orders"
        | "vote_on_draw"
        | "seat_confirmed"
        | "orders_confirmed"
        | "mustering"
        | "resolving";
      timeRemaining: string;
    }
  | { kind: "orders_unconfirmed" }
  | { kind: "paused" }
  | { kind: "waiting_for_players"; joined: number; total: number }
  | { kind: "sandbox" }
  | {
      kind: "finished";
      result: MyGameResult;
      winner?: string;
      departure?: MyGameDeparture;
    };

export interface MyGameEntry {
  id: string;
  name: string;
  status: GameStatus;
  phase?: { season: string; year: number; type: PhaseType };
  nation?: string;
  seatsConfirmed?: { confirmed: number; total: number };
  unreadCount: number;
  state: MyGameState;
}

export interface MyGamesSection {
  key: MyGamesSectionKey;
  games: MyGameEntry[];
}

export interface MyGamesCurrentResponse {
  sections: MyGamesSection[];
}

export interface MyGamesFinishedResponse {
  results: MyGameEntry[];
  next: string | null;
}
