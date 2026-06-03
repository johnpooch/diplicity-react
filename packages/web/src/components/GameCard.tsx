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
import { findNationColor } from "./NationFlag";
import { UserPlus, Lock } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { RemainingTimeDisplay } from "./RemainingTimeDisplay";
import {
  GameList,
  useGameJoinCreate,
  getGamesListQueryKey,
} from "../api/generated/endpoints";
import { formatTimeAgo, getGameLandingPath } from "../util";
import { Skeleton } from "./ui/skeleton";
import { Tooltip, TooltipContent, TooltipTrigger } from "./ui/tooltip";
import { useIsMobile } from "@/hooks/use-mobile";
import { useCheckNotificationPermission } from "@/hooks/useCheckNotificationPermission";

export interface GameCardProps {
  game: GameList;
  variant: Pick<Variant, "name" | "id" | "nations">;
  map: React.ReactNode;
  className?: string;
}

const GameCard: React.FC<GameCardProps> = ({ game, variant, map }) => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const isMobile = useIsMobile();
  const phase = game.currentPhase;
  const playerNation = game.members.find(m => m.isCurrentUser)?.nation ?? null;
  const nationColor = findNationColor(variant.nations, playerNation);
  const joinGameMutation = useGameJoinCreate();
  const checkNotificationPermission = useCheckNotificationPermission();

  const handleClickGame = () => {
    navigate(getGameLandingPath(game, isMobile));
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
      if (!game.sandbox) {
        checkNotificationPermission();
      }
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
                <CardTitle className="flex items-center gap-2">
                  {game.name}
                  {game.sandbox && (
                    <Badge variant="secondary">Sandbox</Badge>
                  )}
                  {!game.sandbox && playerNation && (
                    <Badge className="leading-none" style={{ backgroundColor: nationColor ?? undefined }}>
                      {playerNation}
                    </Badge>
                  )}
                </CardTitle>
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
                  {game.sandbox
                    ? "Resolve when ready"
                    : game.deadlineMode === "fixed_time"
                    ? ({ hourly: "Hourly", daily: "Daily", every_2_days: "Every 2 days", weekly: "Weekly" }[game.movementFrequency ?? ""] ?? "Fixed time")
                    : (game.movementPhaseDuration || "Resolve when ready")}
                </span>
              </div>
              {game.status === "pending" ? (
                <p>Created {formatTimeAgo(game.createdAt)}</p>
              ) : phase ? (
                <p>
                  {phase.season} {phase.year} • {phase.type}
                  {phase.status === "active" && phase.scheduledResolution && (
                    <>
                      {" • "}
                      <RemainingTimeDisplay
                        remainingTime={phase.remainingTime}
                        scheduledResolution={phase.scheduledResolution}
                        isPaused={game.isPaused}
                      />
                    </>
                  )}
                </p>
              ) : (
                <Skeleton className="w-24 h-4" />
              )}
            </CardDescription>
          </div>
        </CardHeader>
        {!game.sandbox && (
          <CardFooter className="p-0 flex justify-between items-center">
            <button
              onClick={handleClickPlayerInfo}
              className="flex -space-x-2"
            >
              {game.members.slice(0, 7).map(member => (
                <Avatar
                  key={member.id}
                  className="h-8 w-8 border-2 border-background"
                >
                  <AvatarImage src={member.picture ?? undefined} />
                  <AvatarFallback>
                    {member.name?.[0]?.toUpperCase() ?? "?"}
                  </AvatarFallback>
                </Avatar>
              ))}
              {game.members.length > 7 && (
                <div className="h-8 w-8 rounded-full bg-muted border-2 border-background flex items-center justify-center text-xs">
                  +{game.members.length - 7}
                </div>
              )}
            </button>
          </CardFooter>
        )}
      </div>
    </Card>
  );
};

export { GameCard };
