import React, { Suspense } from "react";

import { ScreenContainer } from "@/components/ui/screen-container";
import { QueryErrorBoundary } from "@/components/QueryErrorBoundary";
import { GameCard } from "@/components/GameCard";
import { MapView } from "@/components/MapView";
import { Notice } from "@/components/Notice";
import { Inbox, Loader2, Zap } from "lucide-react";
import { useVariantsListSuspense } from "@/api/generated/endpoints";
import { useGamesListInfinite } from "@/hooks/useGamesListInfinite";
import { useInfiniteScroll } from "@/hooks/useInfiniteScroll";

const EXPRESS_MIN_MEMBERS = 3;

const OpenGames: React.FC = () => {
  const { data, fetchNextPage, hasNextPage, isFetchingNextPage } =
    useGamesListInfinite({
      status: "pending",
      ordering: "slots_remaining",
    });
  const { data: variants } = useVariantsListSuspense();

  const games = data.pages.flatMap(page => page.results);
  const variantMap = new Map(variants.map(v => [v.id, v]));
  const knownGames = games.filter(game => variantMap.has(game.variantId));

  const sentinelRef = useInfiniteScroll(
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage
  );

  if (knownGames.length === 0) {
    return (
      <Notice
        title="No open games"
        message="There are no open games to join right now. Sign in to create one."
        icon={Inbox}
      />
    );
  }

  const renderGameCard = (game: (typeof knownGames)[number]) => {
    const variant = variantMap.get(game.variantId)!;
    return (
      <GameCard
        key={game.id}
        game={game}
        variant={variant}
        map={
          <MapView
            mode="static"
            variant={variant}
            phase={variant.templatePhase}
            cover
            className="w-full h-full"
          />
        }
      />
    );
  };

  const hasExpressGame = knownGames[0].members.length >= EXPRESS_MIN_MEMBERS;

  return (
    <div className="space-y-4">
      {hasExpressGame ? (
        <>
          <div className="flex items-center gap-2 pt-2">
            <Zap className="size-4" />
            <h3 className="text-sm font-semibold">
              Fastest Start — Join to start playing quickly
            </h3>
          </div>
          {renderGameCard(knownGames[0])}
          {knownGames.length > 1 && (
            <>
              <h3 className="text-sm font-semibold pt-2">More games</h3>
              {knownGames.slice(1).map(renderGameCard)}
            </>
          )}
        </>
      ) : (
        knownGames.map(renderGameCard)
      )}
      {isFetchingNextPage && (
        <div className="flex justify-center py-4">
          <Loader2 className="animate-spin" />
        </div>
      )}
      <div ref={sentinelRef} />
    </div>
  );
};

const OpenGamesSuspense: React.FC = () => (
  <ScreenContainer>
    <h1 className="text-2xl font-bold">Open Games</h1>
    <QueryErrorBoundary>
      <Suspense fallback={<div></div>}>
        <OpenGames />
      </Suspense>
    </QueryErrorBoundary>
  </ScreenContainer>
);

export { OpenGamesSuspense as OpenGames };
