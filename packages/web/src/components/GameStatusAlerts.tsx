import React from "react";
import { Info, Trophy, Users, AlertTriangle, Pause, UserCog } from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { cn } from "@/lib/utils";
import { isCommitmentLocked } from "@/util";

interface GameStatusAlertsProps {
  game: {
    status: string;
    isPaused?: boolean;
    canJoin?: boolean;
    commitmentEligibility?: string | null;
    victory?: {
      type: string;
      members: readonly { name: string }[];
    } | null;
  };
  variant?: {
    nations: { length: number } | readonly unknown[];
  };
  action?: React.ReactNode;
  adminAction?: React.ReactNode;
  showPausedNotice?: boolean;
}

export function GameStatusAlerts({
  game,
  variant,
  action,
  adminAction,
  showPausedNotice = true,
}: GameStatusAlertsProps) {
  const nationCount = variant?.nations
    ? Array.isArray(variant.nations)
      ? variant.nations.length
      : variant.nations.length
    : undefined;

  const commitmentBlocked =
    game.status === "pending" && game.canJoin && isCommitmentLocked(game);

  return (
    <>
      {game.status === "pending" && (
        <Alert className="p-5">
          <Info className="size-4" />
          <div className="flex flex-col gap-3">
            <AlertDescription>
              This game has not started yet. The game will start once{" "}
              {nationCount} players have joined.
              {commitmentBlocked && (
                <p>
                  You can't join because you don't meet the commitment
                  requirements.
                </p>
              )}
            </AlertDescription>
            {action && <div className="w-full sm:w-auto">{action}</div>}
          </div>
        </Alert>
      )}

      {game.status === "active" && adminAction ? (
        <Alert className={cn("p-5", game.isPaused && "border-destructive")}>
          <UserCog className="size-4" />
          <AlertTitle>Admin</AlertTitle>
          <AlertDescription>
            {game.isPaused
              ? "This game is paused."
              : "Control the game phases here"}
          </AlertDescription>
          <div className="col-start-2 pt-2">{adminAction}</div>
        </Alert>
      ) : (
        showPausedNotice &&
        game.isPaused && (
          <Alert>
            <Pause className="size-4" />
            <AlertDescription>This game is currently paused.</AlertDescription>
          </Alert>
        )
      )}

      {game.victory &&
        (game.victory.type === "solo" ? (
          <Alert className="p-5 border-amber-500/50 bg-amber-500/10 dark:bg-amber-400/10">
            <Trophy className="text-amber-600 dark:text-amber-400" />
            <AlertTitle className="text-base font-semibold text-amber-900 dark:text-amber-200">
              {game.victory.members[0]?.name ?? "A player"} has won!
            </AlertTitle>
            <AlertDescription className="text-amber-700 dark:text-amber-300">
              Solo victory
            </AlertDescription>
          </Alert>
        ) : (
          <Alert className="p-5 border-sky-500/50 bg-sky-500/10 dark:bg-sky-400/10">
            <Users className="text-sky-600 dark:text-sky-400" />
            <AlertTitle className="text-base font-semibold text-sky-900 dark:text-sky-200">
              The game ended in a draw
            </AlertTitle>
            <AlertDescription className="text-sky-700 dark:text-sky-300">
              Between {game.victory.members.length} players
            </AlertDescription>
          </Alert>
        ))}

      {game.status === "abandoned" && (
        <Alert variant="destructive">
          <AlertTriangle className="size-4" />
          <AlertDescription>
            This game was abandoned due to inactivity.
          </AlertDescription>
        </Alert>
      )}
    </>
  );
}
