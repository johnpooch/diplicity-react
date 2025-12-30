import React from "react";
import { Button } from "@/components/ui/button";
import { VariantRead } from "../store";
import {
  Card,
  CardDescription,
  CardHeader,
  CardTitle,
  CardFooter,
} from "@/components/ui/card";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  MoreHorizontal,
  UserPlus,
  Lock,
  Info,
  Users,
  Share,
} from "lucide-react";
import { MemberAvatarGroup } from "./MemberAvatarGroup.new";
import { formatDateTime } from "../util";
import { GameList, useGamePhaseRetrieve } from "../api/generated/endpoints";
import { Skeleton } from "./ui/skeleton";
import { Tooltip, TooltipContent, TooltipTrigger } from "./ui/tooltip";

export interface GameCardProps {
  game: GameList;
  variant: Pick<VariantRead, "name" | "id">;
  phaseId: number;
  map: React.ReactNode;
  onClickGame: (id: string) => void;
  onClickGameInfo: (id: string) => void;
  onClickPlayerInfo: (id: string) => void;
  onClickJoinGame: (id: string) => void;
  className?: string;
}

const GameCard: React.FC<GameCardProps> = ({
  game,
  variant,
  phaseId,
  map,
  onClickGame,
  onClickGameInfo,
  onClickPlayerInfo,
  onClickJoinGame,
}) => {
  const { data: phase } = useGamePhaseRetrieve(game.id, phaseId);

  const handleJoinGame = async () => {
    await onClickJoinGame(game.id);
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
        onClick={() => onClickGame(game.id)}
        className="cursor-pointer hover:opacity-90 transition-opacity md:max-w-xs lg:max-w-sm"
      >
        {map}
      </button>

      <div className="flex flex-col justify-between flex-grow p-4">
        <CardHeader className="p-0">
          <div className="flex flex-col">
            <div className="flex justify-between items-center">
              <CardTitle>{game.name}</CardTitle>
              <div className="flex items-center gap-2">
                {joinGameButton}
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="outline" size="icon">
                      <MoreHorizontal />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <DropdownMenuItem onClick={() => onClickGameInfo(game.id)}>
                      <Info />
                      Game info
                    </DropdownMenuItem>
                    <DropdownMenuItem
                      onClick={() => onClickPlayerInfo(game.id)}
                    >
                      <Users />
                      Player info
                    </DropdownMenuItem>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem
                      onClick={() => {
                        navigator.clipboard.writeText(
                          `${window.location.origin}/game/${game.id}`
                        );
                      }}
                    >
                      <Share />
                      Share
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
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
            onClick={() => onClickPlayerInfo(game.id)}
          />
        </CardFooter>
      </div>
    </Card>
  );
};

export { GameCard };
