import React, { Suspense } from "react";
import { useNavigate } from "react-router";
import { useRequiredParams } from "@/hooks";
import { UserPlus, UserMinus } from "lucide-react";

import { QueryErrorBoundary } from "@/components/QueryErrorBoundary";
import { ScreenHeader } from "@/components/ui/screen-header";
import { ScreenContainer } from "@/components/ui/screen-container";
import { GameDropdownMenu } from "@/components/GameDropdownMenu";
import {
  useGameRetrieveSuspense,
  useGameJoinCreate,
  useGameLeaveDestroy,
} from "@/api/generated/endpoints";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { Button } from "@/components/ui/button";
import { PlayerInfoContent } from "@/components/PlayerInfoContent";

const PlayerInfo: React.FC = () => {
  const { gameId } = useRequiredParams<{ gameId: string }>();

  const navigate = useNavigate();
  const { data: game } = useGameRetrieveSuspense(gameId);
  const joinGameMutation = useGameJoinCreate();
  const leaveGameMutation = useGameLeaveDestroy();

  const handleJoinGame = async () => {
    await joinGameMutation.mutateAsync({ gameId, data: {} });
  };

  const handleLeaveGame = async () => {
    await leaveGameMutation.mutateAsync({ gameId });
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
        title="Player Info"
        showUserAvatar
        actions={
          <>
            {joinLeaveButton}
            <GameDropdownMenu
              game={game}
              onNavigateToGameInfo={handleGameInfo}
              onNavigateToPlayerInfo={handlePlayerInfo}
            />
          </>
        }
      />
      <PlayerInfoContent />
    </ScreenContainer>
  );
};

const PlayerInfoSuspense: React.FC = () => {
  return (
    <div className="w-full">
      <QueryErrorBoundary>
        <Suspense fallback={<div></div>}>
          <PlayerInfo />
        </Suspense>
      </QueryErrorBoundary>
    </div>
  );
};

export { PlayerInfoSuspense as PlayerInfoScreen };
