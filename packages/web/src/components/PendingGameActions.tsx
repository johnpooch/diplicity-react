import React, { useState } from "react";
import { toast } from "sonner";
import { useQueryClient } from "@tanstack/react-query";
import { Bot, Share } from "lucide-react";

import { Button } from "@/components/ui/button";
import { AddBotSheet } from "@/components/AddBotSheet";
import {
  GameRetrieve,
  Variant,
  useGameJoinCreate,
  useGameLeaveDestroy,
  useUserRetrieveSuspense,
  getGameRetrieveQueryKey,
} from "@/api/generated/endpoints";
import { useCheckNotificationPermission } from "@/hooks/useCheckNotificationPermission";

interface PendingGameActionsProps {
  game: GameRetrieve;
  variant?: Variant;
}

export const PendingGameActions: React.FC<PendingGameActionsProps> = ({
  game,
  variant,
}) => {
  const gameId = game.id;
  const queryClient = useQueryClient();
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

  const playableSeats = variant
    ? variant.nations.filter(n => !n.nonPlayable).length
    : 0;
  const openSeats = Math.max(0, playableSeats - game.members.length);
  const canAddBots =
    game.canManage && userProfile.canCreateBotGames && openSeats > 0;

  return (
    <>
      {game.canJoin ? (
        <Button
          onClick={handleJoinGame}
          disabled={joinGameMutation.isPending}
          className="w-full @[500px]:w-auto"
        >
          Join game
        </Button>
      ) : game.canLeave || canAddBots ? (
        <div className="flex flex-wrap gap-2 w-full @[500px]:w-auto">
          {canAddBots && (
            <Button
              onClick={() => setAddBotOpen(true)}
              className="flex-1 @[500px]:flex-none"
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
              className="flex-1 @[500px]:flex-none"
            >
              Leave
            </Button>
          )}
          <Button variant="outline" className="flex-1 @[500px]:flex-none" onClick={handleShare}>
            <Share className="size-4" />
            Share &amp; invite
          </Button>
        </div>
      ) : game.minReliability !== "open" ? (
        <div className="flex flex-col gap-1 w-full @[500px]:w-auto">
          <Button disabled className="w-full @[500px]:w-auto">
            Join game
          </Button>
          <p className="text-xs text-muted-foreground text-center">
            Your reliability is too low to join this game
          </p>
        </div>
      ) : null}
      {canAddBots && (
        <AddBotSheet
          gameId={gameId}
          open={addBotOpen}
          onOpenChange={setAddBotOpen}
        />
      )}
    </>
  );
};
