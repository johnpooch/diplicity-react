import React from "react";
import { Button } from "@/components/ui/button";
import { GameRead, PhaseRetrieveRead, VariantRead } from "../store";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  CardFooter,
} from "@/components/ui/card";
import {
  DropdownMenu,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { MoreHorizontal, UserPlus, Lock } from "lucide-react";
import { cn } from "@/lib/utils";
import { MemberAvatarGroup } from "./MemberAvatarGroup.new";

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
    <Card className="w-full flex shadow-lg flex-col md:flex-row overflow-hidden p-0">
      {/* 1. Map (SVG) Section - Top on mobile, Left on larger screens */}
      <div>{map}</div>

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
                  {/* Using a ghost button for a clean icon action */}
                  <Button variant="ghost" size="icon">
                    <MoreHorizontal />
                  </Button>
                </DropdownMenuTrigger>
                {/* DropdownMenuContent goes here */}
              </DropdownMenu>
            </div>

            <CardDescription className="text-sm text-muted-foreground">
              <div className="flex items-center gap-1">
                {game.private && <Lock className="h-3 w-3" />}
                <span>
                  {variant.name} • {game.movementPhaseDuration}
                </span>
              </div>
              <p>
                {phase.season} {phase.year} • {phase.type}
              </p>
            </CardDescription>
          </div>
        </CardHeader>

        <CardFooter className="p-0 flex justify-start items-center gap-2">
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
