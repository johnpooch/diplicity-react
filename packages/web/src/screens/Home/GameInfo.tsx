import React, { Suspense, useState } from "react";
import { useNavigate } from "react-router";
import { toast } from "sonner";
import { Bot, Share } from "lucide-react";
import { useQueryClient } from "@tanstack/react-query";
import { useRequiredParams } from "@/hooks";

import { QueryErrorBoundary } from "@/components/QueryErrorBoundary";
import { Button } from "@/components/ui/button";
import { GameDropdownMenu } from "@/components/GameDropdownMenu";
import {
  useGameRetrieveSuspense,
  useGameJoinCreate,
  useGameLeaveDestroy,
  useUserRetrieveSuspense,
  getGameRetrieveQueryKey,
} from "@/api/generated/endpoints";
import { useGameVariant } from "@/hooks/useGameVariant";
import { ScreenHeader } from "@/components/ui/screen-header";
import { ScreenContainer } from "@/components/ui/screen-container";
import { AddBotSheet } from "@/components/AddBotSheet";
import { GameInfoContent } from "@/components/GameInfoContent";
import { useCheckNotificationPermission } from "@/hooks/useCheckNotificationPermission";

const GameInfo: React.FC = () => {
  const { gameId } = useRequiredParams<{ gameId: string }>();

  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { data: game } = useGameRetrieveSuspense(gameId);
  const variant = useGameVariant(game);
  const { data: userProfile } = useUserRetrieveSuspense();
  const joinGameMutation = useGameJoinCreate();
  const leaveGameMutation = useGameLeaveDestroy();
  const checkNotificationPermission = useCheckNotificationPermission();

  const [addBotOpen, setAddBotOpen] = useState(false);

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

  const playableSeats = variant
    ? variant.nations.filter(n => !n.nonPlayable).length
    : 0;
  const openSeats = Math.max(0, playableSeats - game.members.length);
  const canAddBots =
    game.status === "pending" &&
    game.canManage &&
    userProfile.canCreateBotGames &&
    openSeats > 0;

  const pendingAction = game.status === "pending" ? (
    game.canJoin ? (
      <Button
        onClick={handleJoinGame}
        disabled={joinGameMutation.isPending}
        className="w-full sm:w-auto"
      >
        Join game
      </Button>
    ) : game.canLeave || canAddBots ? (
      <div className="flex flex-wrap gap-2 w-full sm:w-auto">
        {canAddBots && (
          <Button
            onClick={() => setAddBotOpen(true)}
            className="flex-1 sm:flex-none"
          >
            <Bot className="size-4" />
            Add AI player
          </Button>
        )}
        {game.canLeave && (
          <Button
            onClick={handleLeaveGame}
            disabled={leaveGameMutation.isPending}
            variant="outline"
            className="flex-1 sm:flex-none"
          >
            Leave
          </Button>
        )}
        <Button variant="outline" className="flex-1 sm:flex-none" onClick={handleShare}>
          <Share className="size-4" />
          Share &amp; invite
        </Button>
      </div>
    ) : game.minReliability !== "open" ? (
      <div className="flex flex-col gap-1 w-full sm:w-auto">
        <Button disabled className="w-full sm:w-auto">
          Join game
        </Button>
        <p className="text-xs text-muted-foreground text-center">
          Your reliability is too low to join this game
        </p>
      </div>
    ) : null
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
      {canAddBots && (
        <AddBotSheet
          gameId={gameId}
          open={addBotOpen}
          onOpenChange={setAddBotOpen}
        />
      )}
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
