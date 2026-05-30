import React, { Suspense } from "react";
import { useNavigate } from "react-router";
import { toast } from "sonner";
import { useQueryClient } from "@tanstack/react-query";
import { useRequiredParams } from "@/hooks";

import { QueryErrorBoundary } from "@/components/QueryErrorBoundary";
import { Button } from "@/components/ui/button";
import { GameDropdownMenu } from "@/components/GameDropdownMenu";
import {
  useGameRetrieveSuspense,
  useGameJoinCreate,
  useGameLeaveDestroy,
  getGameRetrieveQueryKey,
} from "@/api/generated/endpoints";
import { ScreenHeader } from "@/components/ui/screen-header";
import { ScreenContainer } from "@/components/ui/screen-container";
import { GameInfoContent } from "@/components/GameInfoContent";
import { useCheckNotificationPermission } from "@/hooks/useCheckNotificationPermission";

const GameInfo: React.FC = () => {
  const { gameId } = useRequiredParams<{ gameId: string }>();

  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { data: game } = useGameRetrieveSuspense(gameId);
  const joinGameMutation = useGameJoinCreate();
  const leaveGameMutation = useGameLeaveDestroy();
  const checkNotificationPermission = useCheckNotificationPermission();

  const handleJoinGame = async () => {
    try {
      await joinGameMutation.mutateAsync({ gameId, data: {} });
      await queryClient.invalidateQueries({ queryKey: getGameRetrieveQueryKey(gameId) });
      toast.success("Game joined successfully");
      if (!game.sandbox) {
        checkNotificationPermission();
      }
    } catch {
      toast.error("Failed to join game");
    }
  };

  const handleLeaveGame = async () => {
    try {
      await leaveGameMutation.mutateAsync({ gameId });
      await queryClient.invalidateQueries({ queryKey: getGameRetrieveQueryKey(gameId) });
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

  const pendingAction = game.status === "pending" ? (
    game.canJoin ? (
      <Button
        onClick={handleJoinGame}
        disabled={joinGameMutation.isPending}
      >
        Join game
      </Button>
    ) : (
      <Button
        onClick={handleLeaveGame}
        disabled={leaveGameMutation.isPending}
        variant="outline"
      >
        Leave game
      </Button>
    )
  ) : null;

  return (
    <ScreenContainer>
      <ScreenHeader
        title="Game Info"
        actions={
          <GameDropdownMenu
            game={game}
            onNavigateToGameInfo={handleGameInfo}
            onNavigateToPlayerInfo={handlePlayerInfo}
          />
        }
      />
      <GameInfoContent
        onNavigateToPlayerInfo={handlePlayerInfo}
        pendingAction={pendingAction}
      />
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
