import React, { Suspense } from "react";
import { useNavigate } from "react-router";
import { GameDetailAppBar } from "./AppBar";
import { Panel } from "@/components/Panel";
import { GameInfoContent } from "@/components/GameInfoContent";
import { useRequiredParams } from "@/hooks";

const GameInfoScreen: React.FC = () => {
  const navigate = useNavigate();
  const { gameId, phaseId } = useRequiredParams<{
    gameId: string;
    phaseId: string;
  }>();

  return (
    <div className="flex flex-col flex-1 min-h-0">
      <GameDetailAppBar
        title="Game Info"
        onNavigateBack={() => navigate(`/game/${gameId}/phase/${phaseId}`)}
        variant="secondary"
      />
      <div className="flex-1 overflow-y-auto">
        <Panel>
          <Panel.Content className="flex flex-col gap-4 px-3 py-4">
            <GameInfoContent
              onOpenVariantDetails={() =>
                navigate(`/game/${gameId}/phase/${phaseId}/game-info/variant`)
              }
            />
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
