import React from "react";
import { Sprout, ShieldCheck, AlertTriangle } from "lucide-react";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";

const RELIABILITY_WINDOW_SIZE = 10;
const RELIABILITY_MIN_GAMES = 3;
const RELIABILITY_ABANDONED_THRESHOLD = 2;

type Tier = "new_player" | "reliable" | "unreliable";

interface ReliabilityBadgeProps {
  tier: string | null;
  gamesFinished: number | null;
  gamesAbandonedRecent: number | null;
}

const TIER_LABEL: Record<Tier, string> = {
  new_player: "New Player",
  reliable: "Reliable",
  unreliable: "Unreliable",
};

const TIER_ICON: Record<Tier, React.ComponentType<{ className?: string }>> = {
  new_player: Sprout,
  reliable: ShieldCheck,
  unreliable: AlertTriangle,
};

const TIER_CLASSES: Record<Tier, string> = {
  new_player:
    "bg-sky-100 text-sky-900 dark:bg-sky-900/40 dark:text-sky-100 border-transparent",
  reliable:
    "bg-emerald-100 text-emerald-900 dark:bg-emerald-900/40 dark:text-emerald-100 border-transparent",
  unreliable:
    "bg-amber-100 text-amber-900 dark:bg-amber-900/40 dark:text-amber-100 border-transparent",
};

const isKnownTier = (tier: string | null): tier is Tier =>
  tier === "new_player" || tier === "reliable" || tier === "unreliable";

const buildTooltipContent = (
  tier: Tier,
  gamesFinished: number,
  gamesAbandonedRecent: number
): { reason: string; path: string | null } => {
  const recent = Math.min(gamesFinished, RELIABILITY_WINDOW_SIZE);
  const completedRecent = Math.max(0, recent - gamesAbandonedRecent);

  if (tier === "new_player") {
    const remaining = Math.max(0, RELIABILITY_MIN_GAMES - gamesFinished);
    return {
      reason: `Has finished ${gamesFinished} ${gamesFinished === 1 ? "game" : "games"} so far.`,
      path:
        remaining > 0
          ? `Finish ${remaining} more ${remaining === 1 ? "game" : "games"} to be classified.`
          : null,
    };
  }

  if (tier === "reliable") {
    return {
      reason: `Completed ${completedRecent} of last ${recent} ${recent === 1 ? "game" : "games"}.`,
      path: null,
    };
  }

  // unreliable
  const completionsNeeded = Math.max(
    0,
    gamesAbandonedRecent - (RELIABILITY_ABANDONED_THRESHOLD - 1)
  );
  return {
    reason: `Abandoned ${gamesAbandonedRecent} of last ${recent} ${recent === 1 ? "game" : "games"}.`,
    path:
      completionsNeeded > 0
        ? `Complete ${completionsNeeded} more ${completionsNeeded === 1 ? "game" : "games"} without abandoning to return to Reliable.`
        : "Complete games without abandoning to return to Reliable.",
  };
};

export const ReliabilityBadge: React.FC<ReliabilityBadgeProps> = ({
  tier,
  gamesFinished,
  gamesAbandonedRecent,
}) => {
  if (!isKnownTier(tier)) {
    return null;
  }

  const Icon = TIER_ICON[tier];
  const label = TIER_LABEL[tier];

  const { reason, path } = buildTooltipContent(
    tier,
    gamesFinished ?? 0,
    gamesAbandonedRecent ?? 0
  );

  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <Badge
          aria-label={`Reliability: ${label}`}
          className={cn("gap-1 cursor-help", TIER_CLASSES[tier])}
        >
          <Icon className="size-3" />
          {label}
        </Badge>
      </TooltipTrigger>
      <TooltipContent>
        <div className="space-y-1 max-w-xs">
          <p className="font-semibold">{label}</p>
          <p>{reason}</p>
          {path && <p>{path}</p>}
        </div>
      </TooltipContent>
    </Tooltip>
  );
};
