import React from "react";
import { Button } from "@/components/ui/button";
import { GameRead, PhaseRetrieveRead, VariantRead } from "../store";
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

export interface GameCardProps {
  game: Pick<
    GameRead,
    "id" | "name" | "private" | "members" | "canJoin" | "movementPhaseDuration"
  >;
  variant: Pick<VariantRead, "name" | "id">;
  phase: Pick<
    PhaseRetrieveRead,
    "season" | "year" | "type" | "scheduledResolution"
  >;
  map: React.ReactNode;
  onClickGame: (id: string) => void;
  onClickGameInfo: (id: string) => void;
  onClickPlayerInfo: (id: string) => void;
  onClickJoinGame: (id: string) => void;
  onMenuClick: (id: string) => void;
  className?: string;
}

const GameCard: React.FC<GameCardProps> = ({
  game,
  variant,
  phase,
  map,
  onClickGame,
  onClickGameInfo,
  onClickPlayerInfo,
  onClickJoinGame,
  onMenuClick,
}) => {
  return (
    <Card className="w-full flex rounded-none shadow-none border-0 border-b flex-col md:flex-row overflow-hidden p-0">
      {/* 1. Map (SVG) Section - Top on mobile, Left on larger screens */}
      <button
        onClick={() => onClickGame(game.id)}
        className="cursor-pointer hover:opacity-90 transition-opacity md:max-w-xs lg:max-w-sm"
      >
        {map}
      </button>

      {/* 2. Content Container - Right Side */}
      <div className="flex flex-col justify-between flex-grow p-4">
        {/* Header (Title, Subtitle, and More Button) */}
        <CardHeader className="p-0">
          <div className="flex flex-col">
            {/* Title and Menu Group */}
            <div className="flex justify-between items-center">
              <CardTitle>{game.name}</CardTitle>
              {/* More Actions Button */}
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" size="icon">
                    <MoreHorizontal />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  <DropdownMenuItem onClick={() => onClickGameInfo(game.id)}>
                    <Info />
                    Game info
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={() => onClickPlayerInfo(game.id)}>
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

            <CardDescription className="text-sm text-muted-foreground">
              <div className="flex items-center gap-1">
                {game.private && <Lock className="h-3 w-3" />}
                <span>
                  {variant.name} •{" "}
                  {game.movementPhaseDuration || "Resolve when ready"}
                </span>
              </div>
              <p>
                {phase.season} {phase.year} • {phase.type}
                {phase.scheduledResolution &&
                  ` • Resolves ${formatDateTime(phase.scheduledResolution)}`}
              </p>
            </CardDescription>
          </div>
        </CardHeader>
        <CardFooter className="p-0 flex justify-between items-center">
          <MemberAvatarGroup
            members={game.members}
            variant={variant.id}
            onClick={() => onClickPlayerInfo(game.id)}
          />

          {game.canJoin && (
            <Button variant="outline" onClick={() => onClickJoinGame(game.id)}>
              <UserPlus />
              Join
            </Button>
          )}
        </CardFooter>
      </div>
    </Card>
  );
};

export { GameCard };
