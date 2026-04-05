import React, { Suspense } from "react";

import { ScreenHeader } from "@/components/ui/screen-header";
import { ScreenContainer } from "@/components/ui/screen-container";
import { QueryErrorBoundary } from "@/components/QueryErrorBoundary";
import { GameCard } from "@/components/GameCard";
import { Notice } from "@/components/Notice";
import { Inbox, Loader2 } from "lucide-react";
import { useVariantsListSuspense } from "@/api/generated/endpoints";
import { useGamesListInfinite } from "@/hooks/useGamesListInfinite";
import { useInfiniteScroll } from "@/hooks/useInfiniteScroll";

const FindGames: React.FC = () => {
  const { data, fetchNextPage, hasNextPage, isFetchingNextPage } =
    useGamesListInfinite({ can_join: true });
  const { data: variants } = useVariantsListSuspense();

  const games = data.pages.flatMap(page => page.results);

  const sentinelRef = useInfiniteScroll(
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage
  );

  const variantMap = new Map(variants.map(v => [v.id, v]));
  const knownGames = games.filter(game => variantMap.has(game.variantId));

  return (
    <div className="space-y-4">
      {knownGames.length > 0 ? (
        <>
          {knownGames.map(game => (
            <GameCard
              key={game.id}
              game={game}
              variant={variantMap.get(game.variantId)!}
              phaseId={game.phases[0]}
              map={<div />}
            />
          ))}
          {isFetchingNextPage && (
            <div className="flex justify-center py-4">
              <Loader2 className="animate-spin" />
            </div>
          )}
          <div ref={sentinelRef} />
        </>
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
