import React, { Suspense } from "react";
import { useNavigate } from "react-router";

import { ScreenHeader } from "@/components/ui/screen-header";
import { ScreenContainer } from "@/components/ui/screen-container";
import { GameCard } from "@/components/GameCard.new";
import { Notice } from "@/components/Notice.new";
import { IconName } from "@/components/Icon";
import {
  GameList,
  useGamesListSuspense,
  useVariantsListSuspense,
} from "@/api/generated/endpoints";

const FindGames: React.FC = () => {
  const navigate = useNavigate();

  const { data: games } = useGamesListSuspense({ can_join: true });
  const { data: variants } = useVariantsListSuspense();

  const getVariant = (game: GameList) => {
    const variant = variants.find(v => v.id === game.variantId);
    if (!variant) {
      throw new Error(`Variant not found for game ${game.id}`);
    }
    return variant;
  };

  const handleClickGame = (id: string) => {
    navigate(`/game/${id}`);
  };

  const handleClickGameInfo = (id: string) => {
    console.log("Game info clicked", id);
  };

  const handleClickPlayerInfo = (id: string) => {
    console.log("Player info clicked", id);
  };

  const handleClickJoinGame = (id: string) => {
    console.log("Join game clicked", id);
  };

  return (
    <div className="space-y-4">
      {games && games.length > 0 ? (
        games.map(game => (
          <GameCard
            key={game.id}
            game={game}
            variant={getVariant(game)}
            phaseId={game.phases[0]}
            map={<div />}
            onClickGame={handleClickGame}
            onClickGameInfo={handleClickGameInfo}
            onClickPlayerInfo={handleClickPlayerInfo}
            onClickJoinGame={handleClickJoinGame}
          />
        ))
      ) : (
        <Notice
          title="No games found"
          message="There are no games available to join. Go to Create Game to start a new game."
          icon={IconName.Empty}
        />
      )}
    </div>
  );
};

const FindGamesSuspense: React.FC = () => {
  return (
    <ScreenContainer>
      <ScreenHeader title="Find Games" />
      <Suspense fallback={<div></div>}>
        <FindGames />
      </Suspense>
    </ScreenContainer>
  );
};

export { FindGamesSuspense as FindGames };
