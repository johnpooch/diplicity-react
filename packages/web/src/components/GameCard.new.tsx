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
import { MoreHorizontal, UserPlus } from "lucide-react"; // ShadCN typically uses Lucide icons
import { Avatar, AvatarFallback } from "@/components/ui/avatar"; // Assuming players are Avatars
import { cn } from "@/lib/utils";

export interface GameCardProps {
  game: Pick<
    GameRead,
    "id" | "name" | "private" | "members" | "canJoin" | "movementPhaseDuration"
  >;
  variant: Pick<VariantRead, "name">;
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

const PlayerAvatarGroup = () => {
  // Renders small circles/avatars for players
  const playerInitials = ["K", "A", "O", "D", "R"]; // Example initials
  return (
    <div className="flex -space-x-2">
      {playerInitials.slice(0, 4).map((initial, index) => (
        <Avatar key={index} className="h-8 w-8 border-2 border-background">
          <AvatarFallback className="text-sm bg-secondary text-secondary-foreground">
            {initial}
          </AvatarFallback>
        </Avatar>
      ))}
      {playerInitials.length > 4 && (
        <div className="h-8 w-8 border-2 border-background rounded-full bg-muted flex items-center justify-center text-xs text-muted-foreground">
          +{playerInitials.length - 4}
        </div>
      )}
    </div>
  );
};
// -----------------------------

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
    // Flex direction roq
    <Card className="w-full flex shadow-lg flex-row overflow-hidden p-0">
      {/* 1. Map (SVG) Section - Left Side */}
      <div>{map}</div>

      {/* 2. Content Container - Right Side */}
      <div className="flex flex-col justify-between flex-grow min-w-0 p-4">
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
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8 ml-4 flex-shrink-0"
                  >
                    <MoreHorizontal className="h-4 w-4" />
                  </Button>
                </DropdownMenuTrigger>
                {/* DropdownMenuContent goes here */}
              </DropdownMenu>
            </div>

            <CardDescription className="text-sm text-muted-foreground">
              <p>
                {variant.name} • {game.movementPhaseDuration}
              </p>
              <p>
                {phase.season} {phase.year} • {phase.type}
              </p>
            </CardDescription>
          </div>
        </CardHeader>

        <CardFooter className="p-0 flex justify-start items-center gap-3 mt-auto">
          <PlayerAvatarGroup />

          {game.canJoin && (
            <Button variant="outline" onClick={() => onClickJoinGame(game.id)}>
              <UserPlus className="h-4 w-4 mr-2" />
              Join
            </Button>
          )}
        </CardFooter>
      </div>
    </Card>
  );
};

export { GameCard };
