import { Info, Trophy, AlertTriangle } from "lucide-react";
import { Alert, AlertDescription } from "@/components/ui/alert";

interface GameStatusAlertsProps {
  game: {
    status: string;
    victory?: {
      type: string;
      members: readonly { name: string }[];
    } | null;
  };
  variant?: {
    nations: { length: number } | readonly unknown[];
  };
}

export function GameStatusAlerts({ game, variant }: GameStatusAlertsProps) {
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
          <AlertDescription>
            This game has not started yet. The game will start once{" "}
            {nationCount} players have joined.
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
