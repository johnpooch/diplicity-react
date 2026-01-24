import React, { Suspense } from "react";
import { useNavigate } from "react-router";
import { toast } from "sonner";
import { useRequiredParams } from "@/hooks";
import { UserPlus, UserMinus } from "lucide-react";

import { QueryErrorBoundary } from "@/components/QueryErrorBoundary";
import { Button } from "@/components/ui/button";
import { GameDropdownMenu } from "@/components/GameDropdownMenu";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  useGameRetrieveSuspense,
  useGameJoinCreate,
  useGameLeaveDestroy,
} from "@/api/generated/endpoints";
import { ScreenHeader } from "@/components/ui/screen-header";
import { ScreenContainer } from "@/components/ui/screen-container";
import { GameInfoContent } from "@/components/GameInfoContent";

const GameInfo: React.FC = () => {
  const { gameId } = useRequiredParams<{ gameId: string }>();

  const navigate = useNavigate();
  const { data: game } = useGameRetrieveSuspense(gameId);
  const joinGameMutation = useGameJoinCreate();
  const leaveGameMutation = useGameLeaveDestroy();

  const handleJoinGame = async () => {
    try {
      await joinGameMutation.mutateAsync({ gameId, data: {} });
      toast.success("Game joined successfully");
    } catch {
      toast.error("Failed to join game");
    }
  };

  const handleLeaveGame = async () => {
    try {
      await leaveGameMutation.mutateAsync({ gameId });
      toast.success("Game left successfully");
    } catch {
      toast.error("Failed to leave game");
    }
  };

  const handlePlayerInfo = () => {
    navigate(`/player-info/${gameId}`);
  };

  const handleGameInfo = () => {
    navigate(`/game-info/${gameId}`);
  };

  const joinLeaveButton = game.canJoin ? (
    <Tooltip>
      <TooltipTrigger asChild>
        <Button
          onClick={handleJoinGame}
          disabled={joinGameMutation.isPending}
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
  ) : (
    <Tooltip>
      <TooltipTrigger asChild>
        <Button
          onClick={handleLeaveGame}
          disabled={leaveGameMutation.isPending}
          variant="outline"
          aria-label="Leave game"
        >
          <UserMinus className="size-4" />
        </Button>
      </TooltipTrigger>
      <TooltipContent>
        <p>Leave game</p>
      </TooltipContent>
    </Tooltip>
  );

  return (
    <ScreenContainer>
      <ScreenHeader
        title="Game Info"
        actions={
          <>
            {joinLeaveButton}
            <GameDropdownMenu
              gameId={game.id}
              canLeave={game.canLeave}
              onNavigateToGameInfo={handleGameInfo}
              onNavigateToPlayerInfo={handlePlayerInfo}
            />
          </>
        }
      />
      <GameInfoContent onNavigateToPlayerInfo={handlePlayerInfo} />
    </ScreenContainer>
  );
};

const GameInfoSuspense: React.FC = () => {
  return (
    <div className="w-full space-y-4">
      <QueryErrorBoundary>
        <Suspense fallback={<div></div>}>
          <GameInfo />
        </Suspense>
      </QueryErrorBoundary>
    </div>
  );
};

export { GameInfoSuspense as GameInfoScreen };
