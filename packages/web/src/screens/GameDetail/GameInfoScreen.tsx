import React, { Suspense, useState } from "react";
import { useNavigate, useParams } from "react-router";
import { useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Bot, UserPlus } from "lucide-react";
import { GameDetailAppBar } from "./AppBar";
import { Button } from "@/components/ui/button";
import { Panel } from "@/components/Panel";
import { Skeleton } from "@/components/ui/skeleton";
import { GameInfoContent } from "@/components/GameInfoContent";
import { AddBotSheet } from "@/components/AddBotSheet";
import { MapView } from "@/components/MapView";
import { useRequiredParams } from "@/hooks";
import { useGameVariant } from "@/hooks/useGameVariant";
import { useCheckNotificationPermission } from "@/hooks/useCheckNotificationPermission";
import { copyLink } from "@/utils/copyLink";
import { isCommitmentLocked } from "@/util";
import {
  useGameRetrieveSuspense,
  useUserRetrieveSuspense,
  useGameMemberJoinCreate,
  useGameLeaveDestroy,
  getGameRetrieveQueryKey,
} from "@/api/generated/endpoints";

const GameInfoScreen: React.FC = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { gameId } = useRequiredParams<{ gameId: string }>();
  const { phaseId } = useParams<{ phaseId: string }>();
  const { data: game } = useGameRetrieveSuspense(gameId);
  const { data: userProfile } = useUserRetrieveSuspense();
  const variant = useGameVariant(game);
  const joinGameMutation = useGameMemberJoinCreate();
  const leaveGameMutation = useGameLeaveDestroy();
  const checkNotificationPermission = useCheckNotificationPermission();

  const [addBotOpen, setAddBotOpen] = useState(false);

  const handleJoinGame = async () => {
    try {
      await joinGameMutation.mutateAsync({ gameId });
      await queryClient.invalidateQueries({
        queryKey: getGameRetrieveQueryKey(gameId),
      });
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
      await queryClient.invalidateQueries({
        queryKey: getGameRetrieveQueryKey(gameId),
      });
      toast.success("Game left successfully");
    } catch {
      toast.error("Failed to leave game");
    }
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

  const canReallyJoin = game.canJoin && !isCommitmentLocked(game);

  const pendingAction =
    game.status === "pending" ? (
      canReallyJoin ? (
        <Button
          onClick={handleJoinGame}
          disabled={joinGameMutation.isPending}
          className="w-full sm:w-auto"
        >
          Join game
        </Button>
      ) : canAddBots || game.canLeave ? (
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
        </div>
      ) : null
    ) : null;

  return (
    <div className="flex flex-col flex-1 min-h-0">
      <GameDetailAppBar
        title={game.name}
        onNavigateBack={() => navigate("/")}
        rightButton={
          game.status !== "pending" && game.canJoin ? (
            <Button
              variant="outline"
              size="icon"
              aria-label="Join game"
              onClick={handleJoinGame}
              disabled={joinGameMutation.isPending}
            >
              <UserPlus />
            </Button>
          ) : undefined
        }
      />
      <div className="flex-1 overflow-y-auto">
        <Panel>
          <Panel.Content className="flex flex-col gap-4 px-3 py-4">
            <GameInfoContent
              showTitle={false}
              pendingAction={pendingAction}
              onOpenVariantDetails={
                phaseId
                  ? () =>
                      navigate(
                        `/game/${gameId}/phase/${phaseId}/game-info/variant`
                      )
                  : undefined
              }
              onShare={() => copyLink(`/game/${gameId}`)}
            />
            {!phaseId && (
              <div className="w-full h-64 overflow-hidden rounded-lg md:hidden">
                {variant ? (
                  <MapView
                    mode="pannable"
                    variant={variant}
                    phase={variant.templatePhase}
                    style={{ width: "100%", height: "100%" }}
                  />
                ) : (
                  <Skeleton className="w-full h-full rounded-lg" />
                )}
              </div>
            )}
          </Panel.Content>
        </Panel>
      </div>
      {canAddBots && (
        <AddBotSheet
          gameId={gameId}
          open={addBotOpen}
          onOpenChange={setAddBotOpen}
        />
      )}
    </div>
  );
};

const GameInfoScreenSuspense: React.FC = () => (
  <Suspense fallback={<div></div>}>
    <GameInfoScreen />
  </Suspense>
);

export { GameInfoScreenSuspense as GameInfoScreen };
