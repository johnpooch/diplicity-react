import React, { Suspense, useState } from "react";
import { useSearchParams } from "react-router";

import { ScreenHeader } from "@/components/ui/screen-header";
import { ScreenContainer } from "@/components/ui/screen-container";
import { QueryErrorBoundary } from "@/components/QueryErrorBoundary";
import { GameCard } from "@/components/GameCard";
import { Notice } from "@/components/Notice";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Inbox, Loader2, SlidersHorizontal } from "lucide-react";
import { useVariantsListSuspense } from "@/api/generated/endpoints";
import type { GamesListMovementPhaseDuration } from "@/api/generated/endpoints";
import { useGamesListInfinite } from "@/hooks/useGamesListInfinite";
import { useInfiniteScroll } from "@/hooks/useInfiniteScroll";
import { DURATION_OPTIONS } from "@/constants";

const VARIANT_PARAM = "variant";
const DURATION_PARAM = "movement_phase_duration";
const ALL_VARIANTS_VALUE = "__all__";
const ANY_DURATION_VALUE = "__any__";

interface FindGamesProps {
  isFilterOpen: boolean;
}

const FindGames: React.FC<FindGamesProps> = ({ isFilterOpen }) => {
  const [searchParams, setSearchParams] = useSearchParams();

  const variantParam = searchParams.get(VARIANT_PARAM) ?? undefined;
  const durationParam =
    (searchParams.get(DURATION_PARAM) as GamesListMovementPhaseDuration) ??
    undefined;

  const { data, fetchNextPage, hasNextPage, isFetchingNextPage } =
    useGamesListInfinite({
      can_join: true,
      ...(variantParam ? { variant: variantParam } : {}),
      ...(durationParam ? { movement_phase_duration: durationParam } : {}),
    });
  const { data: variants } = useVariantsListSuspense();

  const games = data.pages.flatMap(page => page.results);

  const sentinelRef = useInfiniteScroll(
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage
  );

  const variantMap = new Map(variants.map(v => [v.id, v]));
  const knownGames = games.filter(game => variantMap.has(game.variantId));

  const handleVariantChange = (value: string) => {
    setSearchParams(prev => {
      const next = new URLSearchParams(prev);
      if (value === ALL_VARIANTS_VALUE) {
        next.delete(VARIANT_PARAM);
      } else {
        next.set(VARIANT_PARAM, value);
      }
      return next;
    });
  };

  const handleDurationChange = (value: string) => {
    setSearchParams(prev => {
      const next = new URLSearchParams(prev);
      if (value === ANY_DURATION_VALUE) {
        next.delete(DURATION_PARAM);
      } else {
        next.set(DURATION_PARAM, value);
      }
      return next;
    });
  };

  return (
    <div className="space-y-4">
      {isFilterOpen && (
        <div className="grid grid-cols-2 gap-2">
          <Select
            value={variantParam ?? ALL_VARIANTS_VALUE}
            onValueChange={handleVariantChange}
          >
            <SelectTrigger className="w-full">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value={ALL_VARIANTS_VALUE}>All variants</SelectItem>
              {variants.map(v => (
                <SelectItem key={v.id} value={v.id}>
                  {v.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Select
            value={durationParam ?? ANY_DURATION_VALUE}
            onValueChange={handleDurationChange}
          >
            <SelectTrigger className="w-full">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value={ANY_DURATION_VALUE}>Any duration</SelectItem>
              {DURATION_OPTIONS.map(opt => (
                <SelectItem key={opt.value} value={opt.value}>
                  {opt.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      )}

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
  const [isFilterOpen, setIsFilterOpen] = useState(false);

  return (
    <ScreenContainer>
      <ScreenHeader
        title="Find Games"
        showUserAvatar
        actions={
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setIsFilterOpen(prev => !prev)}
            aria-label="Toggle filters"
          >
            <SlidersHorizontal />
          </Button>
        }
      />
      <QueryErrorBoundary>
        <Suspense fallback={<div></div>}>
          <FindGames isFilterOpen={isFilterOpen} />
        </Suspense>
      </QueryErrorBoundary>
    </ScreenContainer>
  );
};

export { FindGamesSuspense as FindGames };
