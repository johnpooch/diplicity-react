import React, { Suspense } from "react";
import { useNavigate, useLocation } from "react-router";
import { toast } from "sonner";
import { Share } from "lucide-react";
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
import { useAuth } from "@/auth";
import { deepLinkStorage } from "@/deepLink";

const GameInfo: React.FC = () => {
  const { gameId } = useRequiredParams<{ gameId: string }>();

  const navigate = useNavigate();
  const location = useLocation();
  const queryClient = useQueryClient();
  const { loggedIn } = useAuth();
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

  const handleShare = async () => {
    try {
      await navigator.clipboard.writeText(`https://diplicity.com/game/${gameId}`);
      toast.success("Link copied to clipboard");
    } catch {
      toast.error("Failed to copy link");
    }
  };

  const handlePlayerInfo = () => {
    navigate(`/player-info/${gameId}`);
  };

  const handleGameInfo = () => {
    navigate(`/game-info/${gameId}`);
  };

  const pendingAction = game.status === "pending" ? (
    !loggedIn ? (
      <Button className="w-full sm:w-auto" onClick={() => {
        deepLinkStorage.setPendingPath(location.pathname);
        navigate("/");
      }}>
        Log in to join
      </Button>
    ) : game.canJoin ? (
      <Button
        onClick={handleJoinGame}
        disabled={joinGameMutation.isPending}
        className="w-full sm:w-auto"
      >
        Join game
      </Button>
    ) : (
      <div className="flex gap-2 w-full sm:w-auto">
        <Button
          onClick={handleLeaveGame}
          disabled={leaveGameMutation.isPending}
          variant="outline"
          className="flex-1 sm:flex-none"
        >
          Leave
        </Button>
        <Button variant="outline" className="flex-1 sm:flex-none" onClick={handleShare}>
          <Share className="size-4" />
          Share &amp; invite
        </Button>
      </div>
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
