import React from "react";
import { Pause, UserX } from "lucide-react";
import { Alert, AlertDescription } from "@/components/ui/alert";
import type { Member, Nation } from "@/api/generated/endpoints";
import { countPlayableNations } from "@/utils/playableNations";
import { formatDateTime, formatList } from "@/util";

interface GameStatusAlertsProps {
  game: {
    status: string;
    isPaused?: boolean;
    musterDeadline?: string | null;
    canWithdraw?: boolean;
    members?: readonly Pick<
      Member,
      "nation" | "civilDisorder" | "replaceable"
    >[];
  };
  variant?: {
    nations: readonly Pick<Nation, "nonPlayable">[];
  };
  action?: React.ReactNode;
  showPausedNotice?: boolean;
}

export function GameStatusAlerts({
  game,
  variant,
  action,
  showPausedNotice = true,
}: GameStatusAlertsProps) {
  const nationCount = variant
    ? countPlayableNations(variant.nations)
    : undefined;
  const civilDisorderNations = game.canWithdraw
    ? (game.members ?? []).flatMap(m =>
        m.civilDisorder && m.replaceable && m.nation ? [m.nation] : []
      )
    : [];

  return (
    <>
      {game.status === "pending" && (
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <p className="text-sm text-muted-foreground">
            The game will start once {nationCount} players have joined.
          </p>
          {action && (
            <div className="shrink-0 w-full sm:w-auto">{action}</div>
          )}
        </div>
      )}

      {game.status === "mustering" && (
        <p className="text-sm text-muted-foreground">
          The game will start once everyone confirms their seat.
          {game.musterDeadline &&
            ` Unconfirmed seats will be vacated at the deadline (${formatDateTime(game.musterDeadline)}).`}
        </p>
      )}

      {showPausedNotice && game.isPaused && (
        <Alert>
          <Pause className="size-4" />
          <AlertDescription>This game is currently paused.</AlertDescription>
        </Alert>
      )}

      {civilDisorderNations.length > 0 && (
        <Alert>
          <UserX />
          <AlertDescription>
            {formatList(civilDisorderNations)}{" "}
            {civilDisorderNations.length > 1 ? "are" : "is"} in civil disorder.
            You can find a replacement player, propose a draw, or withdraw.
            Seats in civil disorder accept draws automatically.
          </AlertDescription>
        </Alert>
      )}

      {game.status === "abandoned" && (
        <Alert variant="destructive">
          <AlertDescription className="!text-foreground">
            This game was abandoned due to inactivity.
          </AlertDescription>
        </Alert>
      )}
    </>
  );
}
