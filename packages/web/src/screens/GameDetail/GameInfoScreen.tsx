import React, { Suspense } from "react";
import { useNavigate } from "react-router";
import { GameDetailAppBar } from "./AppBar";
import { Panel } from "@/components/Panel";
import { GameInfoContent } from "@/components/GameInfoContent";
import { GameDropdownMenu } from "@/components/GameDropdownMenu";
import { QueryErrorBoundary } from "@/components/QueryErrorBoundary";
import { useGameRetrieveSuspense } from "@/api/generated/endpoints";
import { useRequiredParams } from "@/hooks";

const GameInfoScreen: React.FC = () => {
  const navigate = useNavigate();
  const { gameId, phaseId } = useRequiredParams<{
    gameId: string;
    phaseId: string;
  }>();
  const { data: game } = useGameRetrieveSuspense(gameId);
  const isPending = game.status === "pending";

  const handleNavigateToGameInfo = () => {
    navigate(`/game/${gameId}/phase/${phaseId}/game-info`);
  };

  const handleNavigateToPlayerInfo = () => {
    navigate(`/game/${gameId}/phase/${phaseId}/player-info`);
  };

  return (
    <div className="flex flex-col flex-1 min-h-0">
      {isPending ? (
        <GameDetailAppBar
          title={
            <div className="flex items-center gap-2">
              <h1 className="flex-1 text-lg font-semibold truncate">
                {game.name}
              </h1>
              <GameDropdownMenu
                game={game}
                onNavigateToGameInfo={handleNavigateToGameInfo}
                onNavigateToPlayerInfo={handleNavigateToPlayerInfo}
              />
            </div>
          }
          onNavigateBack={() => navigate("/")}
        />
      ) : (
        <GameDetailAppBar
          title={game.name}
          onNavigateBack={() => navigate(`/game/${gameId}/phase/${phaseId}`)}
          variant="secondary"
        />
      )}
      <div className="flex-1 overflow-y-auto">
        <Panel>
          <Panel.Content className="px-4">
            <GameInfoContent onNavigateToPlayerInfo={handleNavigateToPlayerInfo} />
          </Panel.Content>
        </Panel>
      </div>
    </div>
  );
};

const GameInfoScreenSuspense: React.FC = () => (
  <QueryErrorBoundary>
    <Suspense fallback={<div></div>}>
      <GameInfoScreen />
    </Suspense>
  </QueryErrorBoundary>
);

export { GameInfoScreenSuspense as GameInfoScreen };
