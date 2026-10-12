import React, { Suspense } from "react";
import { useNavigate } from "react-router";
import { Share2 } from "lucide-react";
import { GameDetailAppBar } from "./AppBar";
import { ActionList } from "@/components/ActionList";
import { Button } from "@/components/ui/button";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { Panel } from "@/components/Panel";
import { GameInfoContent } from "@/components/GameInfoContent";
import { useRequiredParams } from "@/hooks";
import { copyLink } from "@/utils/copyLink";
import { useGameRetrieveSuspense } from "@/api/generated/endpoints";

const GameInfoScreen: React.FC = () => {
  const navigate = useNavigate();
  const { gameId, phaseId } = useRequiredParams<{
    gameId: string;
    phaseId: string;
  }>();
  const { data: game } = useGameRetrieveSuspense(gameId);

  return (
    <div className="flex flex-col flex-1 min-h-0">
      <GameDetailAppBar
        title={game.name}
        onNavigateBack={() => navigate("/")}
        rightButton={
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="outline"
                size="icon"
                aria-label="Share game"
                onClick={() => copyLink(`/game/${gameId}`)}
              >
                <Share2 />
              </Button>
            </TooltipTrigger>
            <TooltipContent side="bottom">Share game</TooltipContent>
          </Tooltip>
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
            />
            {game.actions.length > 0 && (
              <ActionList gameId={gameId} actions={game.actions} />
            )}
          </Panel.Content>
        </Panel>
      </div>
    </div>
  );
};

const GameInfoScreenSuspense: React.FC = () => (
  <Suspense fallback={<div></div>}>
    <GameInfoScreen />
  </Suspense>
);

export { GameInfoScreenSuspense as GameInfoScreen };
