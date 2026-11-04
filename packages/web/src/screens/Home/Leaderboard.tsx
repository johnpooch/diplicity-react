import React, { Suspense, useCallback, useState } from "react";
import { Link } from "react-router";
import { useSuspenseInfiniteQuery } from "@tanstack/react-query";
import { Loader2, Trophy } from "lucide-react";

import { ScreenHeader } from "@/components/ui/screen-header";
import { ScreenContainer } from "@/components/ui/screen-container";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Notice } from "@/components/Notice";
import { QueryErrorBoundary } from "@/components/QueryErrorBoundary";
import {
  getLeaderboardListQueryKey,
  leaderboardList,
  type LeaderboardEntry,
} from "@/api/generated/endpoints";
import { useInfiniteScroll } from "@/hooks/useInfiniteScroll";
import { cn } from "@/lib/utils";

interface LeaderboardRowProps {
  entry: LeaderboardEntry;
  isOwn: boolean;
  ref?: React.Ref<HTMLAnchorElement>;
}

const LeaderboardRow: React.FC<LeaderboardRowProps> = ({ entry, isOwn, ref }) => (
  <Link
    ref={ref}
    to={`/player/${entry.userId}`}
    aria-current={isOwn ? "true" : undefined}
    className={cn(
      "flex items-center gap-3 px-4 py-3 text-sm transition-colors hover:bg-accent/50",
      isOwn && "bg-accent"
    )}
  >
    <span className="w-10 tabular-nums text-muted-foreground">#{entry.rank}</span>
    <Avatar className="size-8">
      <AvatarImage src={entry.picture ?? undefined} />
      <AvatarFallback>{entry.name[0]?.toUpperCase()}</AvatarFallback>
    </Avatar>
    <span className="flex-1 truncate font-medium">
      {entry.name}
      {isOwn && <span className="font-normal text-muted-foreground"> (you)</span>}
    </span>
    <span className="tabular-nums">{Math.round(entry.rating).toLocaleString()}</span>
  </Link>
);

const Leaderboard: React.FC = () => {
  const { data, fetchNextPage, hasNextPage, isFetchingNextPage } =
    useSuspenseInfiniteQuery({
      queryKey: [...getLeaderboardListQueryKey(), "infinite"],
      queryFn: ({ pageParam }) => leaderboardList({ page: pageParam }),
      initialPageParam: 1,
      getNextPageParam: lastPage => {
        if (!lastPage.next) return undefined;
        const page = new URL(lastPage.next).searchParams.get("page");
        return page ? Number(page) : undefined;
      },
      staleTime: 0,
    });
  const sentinelRef = useInfiniteScroll(fetchNextPage, hasNextPage, isFetchingNextPage);
  const [isOwnRowVisible, setIsOwnRowVisible] = useState(false);
  const ownRowRef = useCallback((element: HTMLAnchorElement | null) => {
    if (!element) return;
    const observer = new IntersectionObserver(([observed]) =>
      setIsOwnRowVisible(observed.isIntersecting)
    );
    observer.observe(element);
    return () => {
      observer.disconnect();
      setIsOwnRowVisible(false);
    };
  }, []);

  const entries = data.pages.flatMap(page => page.results);
  const own = data.pages[0].own;

  if (entries.length === 0) {
    return (
      <Notice
        title="No ranked players yet"
        message="Players appear here once they have played enough ranked games for their rating to be established."
        icon={Trophy}
      />
    );
  }

  return (
    <div className="space-y-4">
      <Card className="overflow-hidden py-0">
        <CardContent className="divide-y p-0">
          {entries.map(entry => {
            const isOwn = entry.userId === own?.userId;
            return (
              <LeaderboardRow
                key={entry.userId}
                entry={entry}
                isOwn={isOwn}
                ref={isOwn ? ownRowRef : undefined}
              />
            );
          })}
        </CardContent>
      </Card>
      {isFetchingNextPage && (
        <div className="flex justify-center py-4">
          <Loader2 className="animate-spin" />
        </div>
      )}
      <div ref={sentinelRef} />
      {own && !isOwnRowVisible && (
        <Card className="sticky bottom-4 overflow-hidden py-0 shadow-lg">
          <CardContent className="p-0">
            <LeaderboardRow entry={own} isOwn />
          </CardContent>
        </Card>
      )}
    </div>
  );
};

const LeaderboardSkeleton: React.FC = () => (
  <Card className="overflow-hidden py-0">
    <CardContent className="divide-y p-0">
      {[0, 1, 2, 3, 4].map(index => (
        <div key={index} className="flex items-center gap-3 px-4 py-3">
          <Skeleton className="h-4 w-10" />
          <Skeleton className="size-8 rounded-full" />
          <Skeleton className="h-4 flex-1" />
          <Skeleton className="h-4 w-12" />
        </div>
      ))}
    </CardContent>
  </Card>
);

const LeaderboardSuspense: React.FC = () => (
  <ScreenContainer>
    <ScreenHeader title="Leaderboard" />
    <QueryErrorBoundary>
      <Suspense fallback={<LeaderboardSkeleton />}>
        <Leaderboard />
      </Suspense>
    </QueryErrorBoundary>
  </ScreenContainer>
);

export { LeaderboardSuspense as Leaderboard };
