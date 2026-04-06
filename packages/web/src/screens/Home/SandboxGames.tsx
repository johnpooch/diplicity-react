import React, { Suspense } from "react";
import { useNavigate } from "react-router";

import { ScreenHeader } from "@/components/ui/screen-header";
import { ScreenContainer } from "@/components/ui/screen-container";
import { QueryErrorBoundary } from "@/components/QueryErrorBoundary";
import { GameCard } from "@/components/GameCard";
import { Notice } from "@/components/Notice";
import { Blocks, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useVariantsListSuspense } from "@/api/generated/endpoints";
import { useGamesListInfinite } from "@/hooks/useGamesListInfinite";
import { useInfiniteScroll } from "@/hooks/useInfiniteScroll";

const SandboxGames: React.FC = () => {
  const navigate = useNavigate();

  const { data, fetchNextPage, hasNextPage, isFetchingNextPage } =
    useGamesListInfinite({ sandbox: true, mine: true });
  const { data: variants } = useVariantsListSuspense();

  const games = data.pages.flatMap(page => page.results);

  const sentinelRef = useInfiniteScroll(
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage
  );

  const variantMap = new Map(variants.map(v => [v.id, v]));
  const knownGames = games.filter(game => variantMap.has(game.variantId));

  const handleClickCreateSandbox = () => {
    navigate("/create-game?sandbox=true");
  };

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
          title="No sandbox games found"
          message="Practice by controlling all nations. No time limits—resolve when ready."
          icon={Blocks}
          actions={
            <Button onClick={handleClickCreateSandbox}>
              Create a sandbox game
            </Button>
          }
        />
      )}
    </div>
  );
};

const SandboxGamesSuspense: React.FC = () => {
  return (
    <ScreenContainer>
      <ScreenHeader title="Sandbox Games" showUserAvatar />
      <QueryErrorBoundary>
        <Suspense fallback={<div></div>}>
          <SandboxGames />
        </Suspense>
      </QueryErrorBoundary>
    </ScreenContainer>
  );
};

export { SandboxGamesSuspense as SandboxGames };
