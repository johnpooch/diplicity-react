import React, { Suspense } from "react";

import { ScreenHeader } from "@/components/ui/screen-header";
import { ScreenContainer } from "@/components/ui/screen-container";
import { QueryErrorBoundary } from "@/components/QueryErrorBoundary";
import { GameCard } from "@/components/GameCard";
import { Notice } from "@/components/Notice";
import { Inbox } from "lucide-react";
import {
  GameList,
  useGamesListSuspense,
  useVariantsListSuspense,
} from "@/api/generated/endpoints";

const FindGames: React.FC = () => {
  const { data: games } = useGamesListSuspense({ can_join: true });
  const { data: variants } = useVariantsListSuspense();

  const getVariant = (game: GameList) => {
    const variant = variants.find(v => v.id === game.variantId);
    if (!variant) {
      throw new Error(`Variant not found for game ${game.id}`);
    }
    return variant;
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
          />
        ))
      ) : (
        <Notice
          title="No games found"
          message="There are no games available to join. Go to Create Game to start a new game."
          icon={Inbox}
        />
      )}
    </div>
  );
};

const FindGamesSuspense: React.FC = () => {
  return (
    <ScreenContainer>
      <ScreenHeader title="Find Games" />
      <QueryErrorBoundary>
        <Suspense fallback={<div></div>}>
          <FindGames />
        </Suspense>
      </QueryErrorBoundary>
    </ScreenContainer>
  );
};

export { FindGamesSuspense as FindGames };
