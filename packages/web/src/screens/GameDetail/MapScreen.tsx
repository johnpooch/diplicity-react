import React, { Suspense } from "react";
import { useNavigate } from "react-router";
import { QueryErrorBoundary } from "@/components/QueryErrorBoundary";
import { GameDetailAppBar } from "./AppBar";
import { Panel } from "@/components/Panel";
import { PhaseSelect } from "@/components/PhaseSelect";
import { PhaseGuidance } from "@/components/PhaseGuidance";
import { GameMap } from "@/components/GameMap";
import { GameDropdownMenu } from "@/components/GameDropdownMenu";
import { useGameRetrieveSuspense } from "../../api/generated/endpoints";
import { useRequiredParams } from "../../hooks";

const MapScreen: React.FC = () => {
  const navigate = useNavigate();
  const { gameId, phaseId } = useRequiredParams<{
    gameId: string;
    phaseId: string;
  }>();
  const { data: game } = useGameRetrieveSuspense(gameId);

  const handleNavigateToGameInfo = () => {
    navigate(`/game/${gameId}/phase/${phaseId}/game-info`);
  };

  const handleNavigateToPlayerInfo = () => {
    navigate(`/game/${gameId}/phase/${phaseId}/player-info`);
  };

  return (
    <div className="flex flex-col flex-1 min-h-0">
      <GameDetailAppBar
        title={
          <div className="flex items-center gap-2">
            <div className="flex-1 flex flex-col items-center gap-0.5">
              <PhaseSelect />
              <Suspense fallback={null}>
                <PhaseGuidance />
              </Suspense>
            </div>
            <GameDropdownMenu
              gameId={gameId}
              canLeave={game.canLeave}
              onNavigateToGameInfo={handleNavigateToGameInfo}
              onNavigateToPlayerInfo={handleNavigateToPlayerInfo}
            />
          </div>
        }
        onNavigateBack={() => navigate("/")}
      />
      <div className="flex-1 overflow-y-auto">
        <Panel>
          <Panel.Content>
            <GameMap />
          </Panel.Content>
        </Panel>
      </div>
    </div>
  );
};

const MapScreenSuspense: React.FC = () => (
  <QueryErrorBoundary>
    <Suspense fallback={<div></div>}>
      <MapScreen />
    </Suspense>
  </QueryErrorBoundary>
);

export { MapScreenSuspense as MapScreen };
