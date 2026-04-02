import React, { Suspense } from "react";

import { ScreenHeader } from "@/components/ui/screen-header";
import { ScreenContainer } from "@/components/ui/screen-container";
import { QueryErrorBoundary } from "@/components/QueryErrorBoundary";
import { GameCard } from "@/components/GameCard";
import { Notice } from "@/components/Notice";
import { Inbox } from "lucide-react";
import {
  useGamesListSuspense,
  useVariantsListSuspense,
} from "@/api/generated/endpoints";

const FindGames: React.FC = () => {
  const { data: games } = useGamesListSuspense({ can_join: true });
  const { data: variants } = useVariantsListSuspense();

  const variantMap = new Map(variants.map(v => [v.id, v]));
  const knownGames = games.filter(game => variantMap.has(game.variantId));

  return (
    <div className="space-y-4">
      {knownGames.length > 0 ? (
        knownGames.map(game => (
          <GameCard
            key={game.id}
            game={game}
            variant={variantMap.get(game.variantId)!}
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
      <ScreenHeader title="Find Games" showUserAvatar />
      <QueryErrorBoundary>
        <Suspense fallback={<div></div>}>
          <FindGames />
        </Suspense>
      </QueryErrorBoundary>
    </ScreenContainer>
  );
};

export { FindGamesSuspense as FindGames };
