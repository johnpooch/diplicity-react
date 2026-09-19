import React, { Suspense } from "react";
import { useNavigate } from "react-router";
import { Share2 } from "lucide-react";
import { GameDetailAppBar } from "./AppBar";
import { Button } from "@/components/ui/button";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { Panel } from "@/components/Panel";
import { PlayerInfoContent } from "@/components/PlayerInfoContent";
import { useRequiredParams } from "@/hooks";
import { copyLink } from "@/utils/copyLink";

const PlayerInfoScreen: React.FC = () => {
  const navigate = useNavigate();
  const { gameId } = useRequiredParams<{ gameId: string }>();

  return (
    <div className="flex flex-col flex-1 min-h-0">
      <GameDetailAppBar
        title="Players"
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
            <PlayerInfoContent />
          </Panel.Content>
        </Panel>
      </div>
    </div>
  );
};

const PlayerInfoScreenSuspense: React.FC = () => (
  <Suspense fallback={<div></div>}>
    <PlayerInfoScreen />
  </Suspense>
);

export { PlayerInfoScreenSuspense as PlayerInfoScreen };
