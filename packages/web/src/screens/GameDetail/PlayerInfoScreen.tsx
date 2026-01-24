import React, { Suspense } from "react";
import { useNavigate } from "react-router";
import { GameDetailAppBar } from "./AppBar";
import { Panel } from "@/components/Panel";
import { PlayerInfoContent } from "@/components/PlayerInfoContent";
import { useRequiredParams } from "@/hooks";

const PlayerInfoScreen: React.FC = () => {
  const navigate = useNavigate();
  const { gameId, phaseId } = useRequiredParams<{
    gameId: string;
    phaseId: string;
  }>();

  return (
    <div className="flex flex-col flex-1 min-h-0">
      <GameDetailAppBar
        title="Player Info"
        onNavigateBack={() => navigate(`/game/${gameId}/phase/${phaseId}`)}
        variant="secondary"
      />
      <div className="flex-1 overflow-y-auto">
        <Panel>
          <Panel.Content>
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
