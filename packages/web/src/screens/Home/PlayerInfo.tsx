import React, { Suspense } from "react";
import { useNavigate } from "react-router";
import { useRequiredParams } from "@/hooks";

import { QueryErrorBoundary } from "@/components/QueryErrorBoundary";
import { ScreenHeader } from "@/components/ui/screen-header";
import { ScreenContainer } from "@/components/ui/screen-container";
import { GameDropdownMenu } from "@/components/GameDropdownMenu";
import { useGameRetrieveSuspense } from "@/api/generated/endpoints";
import { PlayerInfoContent } from "@/components/PlayerInfoContent";
import { getGameInfoPath } from "@/util";

const PlayerInfo: React.FC = () => {
  const { gameId } = useRequiredParams<{ gameId: string }>();

  const navigate = useNavigate();
  const { data: game } = useGameRetrieveSuspense(gameId);

  const handlePlayerInfo = () => {
    navigate(`/player-info/${gameId}`);
  };

  const handleGameInfo = () => {
    navigate(getGameInfoPath(game));
  };

  return (
    <ScreenContainer>
      <ScreenHeader
        title="Player Info"
        actions={
          <GameDropdownMenu
            game={game}
            onNavigateToGameInfo={handleGameInfo}
            onNavigateToPlayerInfo={handlePlayerInfo}
          />
        }
      />
      <PlayerInfoContent />
    </ScreenContainer>
  );
};

const PlayerInfoSuspense: React.FC = () => {
  return (
    <div className="w-full">
      <QueryErrorBoundary>
        <Suspense fallback={<div></div>}>
          <PlayerInfo />
        </Suspense>
      </QueryErrorBoundary>
    </div>
  );
};

export { PlayerInfoSuspense as PlayerInfoScreen };
