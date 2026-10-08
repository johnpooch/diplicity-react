import React, { Suspense, useState } from "react";
import { useNavigate } from "react-router";
import { useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { UserPlus } from "lucide-react";
import { GameDetailAppBar } from "./AppBar";
import { Button } from "@/components/ui/button";
import { Panel } from "@/components/Panel";
import { GameInfoContent } from "@/components/GameInfoContent";
import { useRequiredParams } from "@/hooks";
import { useCheckNotificationPermission } from "@/hooks/useCheckNotificationPermission";
import { ShortGameJoinWarningDialog } from "@/components/ShortGameJoinWarningDialog";
import { copyLink } from "@/utils/copyLink";
import {
  useGameRetrieveSuspense,
  useGameMemberJoinCreate,
  getGameRetrieveQueryKey,
} from "@/api/generated/endpoints";

const GameInfoScreen: React.FC = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { gameId, phaseId } = useRequiredParams<{
    gameId: string;
    phaseId: string;
  }>();
  const { data: game } = useGameRetrieveSuspense(gameId);
  const joinGameMutation = useGameMemberJoinCreate();
  const checkNotificationPermission = useCheckNotificationPermission();
  const [showJoinWarning, setShowJoinWarning] = useState(false);

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

  const handleClickJoinGame = () => {
    if (game.showShortGameJoinWarning) {
      setShowJoinWarning(true);
    } else {
      handleJoinGame();
    }
  };

  return (
    <div className="flex flex-col flex-1 min-h-0">
      <GameDetailAppBar
        title={game.name}
        onNavigateBack={() => navigate("/")}
        rightButton={
          game.canJoin ? (
            <Button
              variant="outline"
              size="icon"
              aria-label="Join game"
              onClick={handleClickJoinGame}
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
              onOpenVariantDetails={() =>
                navigate(`/game/${gameId}/phase/${phaseId}/game-info/variant`)
              }
              onShare={() => copyLink(`/game/${gameId}`)}
            />
          </Panel.Content>
        </Panel>
      </div>
      <ShortGameJoinWarningDialog
        open={showJoinWarning}
        onOpenChange={setShowJoinWarning}
        onConfirm={handleJoinGame}
      />
    </div>
  );
};

const GameInfoScreenSuspense: React.FC = () => (
  <Suspense fallback={<div></div>}>
    <GameInfoScreen />
  </Suspense>
);

export { GameInfoScreenSuspense as GameInfoScreen };
