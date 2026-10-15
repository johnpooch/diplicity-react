import React from "react";
import { Pause } from "lucide-react";
import { Alert, AlertDescription } from "@/components/ui/alert";
import type { Nation } from "@/api/generated/endpoints";
import { countPlayableNations } from "@/utils/playableNations";

interface GameStatusAlertsProps {
  game: {
    status: string;
    isPaused?: boolean;
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

      {showPausedNotice && game.isPaused && (
        <Alert>
          <Pause className="size-4" />
          <AlertDescription>This game is currently paused.</AlertDescription>
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
