import React from "react";
import { useNavigate } from "react-router";
import { toast } from "sonner";
import { useQueryClient } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { Variant } from "../api/generated/endpoints";
import {
  Card,
  CardDescription,
  CardHeader,
  CardTitle,
  CardFooter,
} from "@/components/ui/card";
import { GameDropdownMenu } from "./GameDropdownMenu";
import { UserPlus, Lock } from "lucide-react";
import { MemberAvatarGroup } from "./MemberAvatarGroup";
import { formatDateTime } from "../util";
import {
  GameList,
  useGameJoinCreate,
  useGamePhaseRetrieve,
  getGamesListQueryKey,
} from "../api/generated/endpoints";
import { Skeleton } from "./ui/skeleton";
import { Tooltip, TooltipContent, TooltipTrigger } from "./ui/tooltip";

export interface GameCardProps {
  game: GameList;
  variant: Pick<Variant, "name" | "id">;
  phaseId: number;
  map: React.ReactNode;
  className?: string;
}

const GameCard: React.FC<GameCardProps> = ({ game, variant, phaseId, map }) => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { data: phase } = useGamePhaseRetrieve(game.id, phaseId);
  const joinGameMutation = useGameJoinCreate();

  const handleClickGame = () => {
    if (game.status === "pending") {
      navigate(`/game-info/${game.id}`);
    } else {
      navigate(`/game/${game.id}`);
    }
  };

  const handleClickGameInfo = () => {
    navigate(`/game-info/${game.id}`);
  };

  const handleClickPlayerInfo = () => {
    navigate(`/player-info/${game.id}`);
  };

  const handleJoinGame = async () => {
    try {
      await joinGameMutation.mutateAsync({ gameId: game.id, data: {} });
      toast.success("Successfully joined game");
      queryClient.invalidateQueries({ queryKey: getGamesListQueryKey() });
    } catch {
      toast.error("Failed to join game");
    }
  };

  const joinGameButton = game.canJoin && (
    <Tooltip>
      <TooltipTrigger asChild>
        <Button
          onClick={handleJoinGame}
          variant="outline"
          aria-label="Join game"
        >
          <UserPlus className="size-4" />
        </Button>
      </TooltipTrigger>
      <TooltipContent>
        <p>Join game</p>
      </TooltipContent>
    </Tooltip>
  );

  return (
    <Card className="w-full flex  flex-col md:flex-row overflow-hidden p-0">
      <button
        onClick={handleClickGame}
        className="cursor-pointer hover:opacity-90 transition-opacity md:max-w-xs lg:max-w-sm"
      >
        {map}
      </button>

      <div className="flex flex-col justify-between flex-grow p-4">
        <CardHeader className="p-0">
          <div className="flex flex-col">
            <div className="flex justify-between items-center">
              <button
                onClick={handleClickGame}
                className="text-left hover:underline"
              >
                <CardTitle>{game.name}</CardTitle>
              </button>
              <div className="flex items-center gap-2">
                {joinGameButton}
                <GameDropdownMenu
                  game={game}
                  onNavigateToGameInfo={handleClickGameInfo}
                  onNavigateToPlayerInfo={handleClickPlayerInfo}
                />
              </div>
            </div>

            <CardDescription className="text-sm text-muted-foreground">
              <div className="flex items-center gap-1">
                {game.private && <Lock className="h-3 w-3" />}
                <span>
                  {variant.name} •{" "}
                  {game.movementPhaseDuration || "Resolve when ready"}
                </span>
              </div>
              {phase ? (
                <p>
                  {phase.season} {phase.year} • {phase.type}
                  {phase.scheduledResolution &&
                    ` • Resolves ${formatDateTime(phase.scheduledResolution)}`}
                </p>
              ) : (
                <Skeleton className="w-24 h-4" />
              )}
            </CardDescription>
          </div>
        </CardHeader>
        <CardFooter className="p-0 flex justify-between items-center">
          <MemberAvatarGroup
            members={game.members}
            variant={variant.id}
            onClick={handleClickPlayerInfo}
          />
        </CardFooter>
      </div>
    </Card>
  );
};

export { GameCard };
