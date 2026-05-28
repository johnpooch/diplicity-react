import React from "react";
import { Info, Trophy, AlertTriangle, Pause } from "lucide-react";
import { Alert, AlertDescription } from "@/components/ui/alert";

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
}

export function GameStatusAlerts({ game, variant, action }: GameStatusAlertsProps) {
  const nationCount = variant?.nations
    ? Array.isArray(variant.nations)
      ? variant.nations.length
      : variant.nations.length
    : undefined;

  return (
    <>
      {game.status === "pending" && (
        <Alert>
          <Info className="size-4" />
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
            <AlertDescription>
              This game has not started yet. The game will start once{" "}
              {nationCount} players have joined.
            </AlertDescription>
            {action}
          </div>
        </Alert>
      )}

      {game.isPaused && (
        <Alert>
          <Pause className="size-4" />
          <AlertDescription>
            This game is currently paused.
          </AlertDescription>
        </Alert>
      )}

      {game.victory && (
        <Alert>
          <Trophy className="size-4" />
          <AlertDescription>
            {game.victory.type === "solo"
              ? `${game.victory.members[0]?.name} has won the game!`
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
