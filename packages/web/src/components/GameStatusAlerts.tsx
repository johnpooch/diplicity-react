import React from "react";
import { Info, Trophy, AlertTriangle, Pause, UserCog } from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { cn } from "@/lib/utils";

interface GameStatusAlertsProps {
  game: {
    status: string;
    isPaused?: boolean;
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
}

export function GameStatusAlerts({
  game,
  variant,
  action,
  adminAction,
}: GameStatusAlertsProps) {
  const nationCount = variant?.nations
    ? Array.isArray(variant.nations)
      ? variant.nations.length
      : variant.nations.length
    : undefined;

  return (
    <>
      {game.status === "pending" && (
        <Alert className="p-5">
          <Info className="size-4" />
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
            <AlertDescription>
              This game has not started yet. The game will start once{" "}
              {nationCount} players have joined.
            </AlertDescription>
            {action && (
              <div className="shrink-0 w-full sm:w-auto">
                {action}
              </div>
            )}
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
              : "You can pause this game or extend the current deadline."}
          </AlertDescription>
          <div className="col-start-2 pt-2">{adminAction}</div>
        </Alert>
      ) : (
        game.isPaused && (
          <Alert>
            <Pause className="size-4" />
            <AlertDescription>This game is currently paused.</AlertDescription>
          </Alert>
        )
      )}

      {game.victory && (
        <Alert>
          <Trophy className="size-4" />
          <AlertDescription>
            {game.victory.type === "solo"
              ? `${game.victory.members[0]?.name ?? "A player"} has won the game!`
              : `The game ended in a draw between ${game.victory.members.length} players.`}
          </AlertDescription>
        </Alert>
      )}

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
