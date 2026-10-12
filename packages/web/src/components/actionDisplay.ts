import {
  CircleCheck,
  Clock,
  Flag,
  Link2,
  LogOut,
  Pause,
  Play,
  UserCog,
  UserMinus,
  UserPlus,
  type LucideIcon,
} from "lucide-react";
import { WITHDRAW_CONFIRMATION } from "@/components/WithdrawGameAction";
import type {
  BlockedReasonEnum,
  MemberActionKeyEnum,
} from "@/api/generated/endpoints";

interface ActionMember {
  id: number;
  name: string;
  nation: string | null;
}

interface ActionDisplay {
  label: string;
  icon: LucideIcon;
  primary?: boolean;
  success?: (member?: ActionMember) => string;
  error?: string;
}

interface ActionConfirmation {
  title: string;
  description: string;
  confirmLabel: string;
}

const removedToast = (member?: ActionMember) =>
  `${member?.name} removed from the game`;

const ACTION_DISPLAY: Record<MemberActionKeyEnum, ActionDisplay> = {
  join: {
    label: "Join game",
    icon: UserPlus,
    primary: true,
    success: () => "Game joined successfully",
    error: "Failed to join game",
  },
  confirm_seat: {
    label: "Confirm seat",
    icon: CircleCheck,
    primary: true,
    error: "Failed to confirm seat",
  },
  edit_nation_preferences: { label: "Nation preferences", icon: Flag },
  assign_nations: { label: "Assign nations", icon: UserCog },
  extend_deadline: {
    label: "Extend deadline",
    icon: Clock,
    success: () => "Deadline extended",
    error: "Failed to extend deadline",
  },
  pause: {
    label: "Pause game",
    icon: Pause,
    success: () => "Game paused",
    error: "Failed to pause game",
  },
  unpause: {
    label: "Resume game",
    icon: Play,
    primary: true,
    success: () => "Game resumed",
    error: "Failed to resume game",
  },
  leave: {
    label: "Leave game",
    icon: LogOut,
    success: () => "Successfully left game",
    error: "Failed to leave game",
  },
  withdraw: {
    label: "Withdraw from game",
    icon: LogOut,
    error: "Failed to withdraw from game",
  },
  take_over: { label: "Take over seat", icon: UserPlus, primary: true },
  share_replacement_link: { label: "Invite replacement", icon: Link2 },
  remove_from_lobby: {
    label: "Remove player",
    icon: UserMinus,
    success: removedToast,
    error: "Failed to remove player",
  },
  remove_from_game: {
    label: "Remove player",
    icon: UserMinus,
    success: removedToast,
    error: "Failed to remove player",
  },
};

const BLOCKED_REASONS: Record<BlockedReasonEnum, string> = {
  commitment_too_low:
    "Your commitment rating does not meet this game's requirement.",
  no_missed_orders: "This player has not missed any orders.",
};

const confirmationFor = (
  key: MemberActionKeyEnum,
  member?: ActionMember
): ActionConfirmation | null => {
  const removeTitle = `Remove ${member?.nation ?? member?.name}`;
  switch (key) {
    case "leave":
      return {
        title: "Leave game",
        description:
          "You give up your seat. You can join again while the game has an open seat.",
        confirmLabel: "Leave",
      };
    case "withdraw":
      return WITHDRAW_CONFIRMATION;
    case "remove_from_lobby":
      return {
        title: removeTitle,
        description: `${member?.name} is removed from the lobby. They can join again while the game has an open seat.`,
        confirmLabel: "Remove",
      };
    case "remove_from_game":
      return {
        title: removeTitle,
        description:
          "Their orders for this phase are discarded and the seat opens for a replacement. They can view the game but cannot rejoin.",
        confirmLabel: "Remove",
      };
    default:
      return null;
  }
};

export { ACTION_DISPLAY, BLOCKED_REASONS, confirmationFor };
export type { ActionMember };
