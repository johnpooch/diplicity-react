import React, { Suspense, useState } from "react";
import { Link, useSearchParams } from "react-router";
import { useSuspenseInfiniteQuery } from "@tanstack/react-query";
import * as VisuallyHidden from "@radix-ui/react-visually-hidden";
import { Check, CircleCheck, History, Inbox, ListFilter, Loader2 } from "lucide-react";

import { ScreenHeader } from "@/components/ui/screen-header";
import { ScreenContainer } from "@/components/ui/screen-container";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Sheet, SheetContent, SheetDescription, SheetTitle, SheetTrigger } from "@/components/ui/sheet";
import { MyGameCard } from "@/components/MyGameCard";
import { Notice } from "@/components/Notice";
import { QueryErrorBoundary } from "@/components/QueryErrorBoundary";
import {
  gamesMineFinishedList,
  getGamesMineFinishedListQueryKey,
  useGamesMineCurrentRetrieveSuspense,
  type KeyEnum,
} from "@/api/generated/endpoints";
import { useInfiniteScroll } from "@/hooks/useInfiniteScroll";
import { useIsMobile } from "@/hooks/use-mobile";

const views = [
  { key: "current", label: "Current" },
  { key: "finished", label: "Finished" },
] as const;

type View = (typeof views)[number]["key"];

const sectionTitles: Record<KeyEnum, string> = {
  needs_attention: "Needs attention",
  managing: "Managing",
  active: "Active",
  mustering: "Mustering",
  pending: "Pending",
  recently_finished: "Recently finished",
  sandbox: "Sandbox",
};

const useView = (): View =>
  useSearchParams()[0].get("view") === "finished" ? "finished" : "current";

const ViewSelector: React.FC = () => {
  const view = useView();
  const [, setSearchParams] = useSearchParams();
  const isMobile = useIsMobile();
  const [open, setOpen] = useState(false);
  const selected = views.find(option => option.key === view) ?? views[0];
  const label = `Choose game view, ${selected.label} selected`;

  const handleSelect = (next: View) => {
    setSearchParams(next === "finished" ? { view: next } : {});
    setOpen(false);
  };

  const options = (
    <div className="grid gap-1">
      {views.map(option => (
        <Button
          key={option.key}
          variant={view === option.key ? "secondary" : "ghost"}
          aria-pressed={view === option.key}
          onClick={() => handleSelect(option.key)}
          className="justify-between"
        >
          {option.label}
          {view === option.key && <Check />}
        </Button>
      ))}
    </div>
  );

  if (isMobile) {
    return (
      <Sheet open={open} onOpenChange={setOpen}>
        <SheetTrigger asChild>
          <Button variant="ghost" size="icon" className="relative" aria-label={label}>
            <ListFilter />
            {view === "finished" && (
              <span className="absolute top-1.5 right-1.5 size-2 rounded-full bg-primary ring-2 ring-background" />
            )}
          </Button>
        </SheetTrigger>
        <SheetContent side="bottom" className="rounded-t-lg p-2">
          <VisuallyHidden.Root>
            <SheetTitle>View games</SheetTitle>
            <SheetDescription>Choose which games to show</SheetDescription>
          </VisuallyHidden.Root>
          {options}
        </SheetContent>
      </Sheet>
    );
  }

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button variant="ghost" size="sm" aria-label={label}>
          {selected.label}
          <ListFilter />
        </Button>
      </PopoverTrigger>
      <PopoverContent align="end" className="w-64 p-2">
        {options}
      </PopoverContent>
    </Popover>
  );
};

const CurrentGames: React.FC = () => {
  const { data } = useGamesMineCurrentRetrieveSuspense({ query: { staleTime: 0 } });

  if (data.sections.length === 0) {
    return (
      <Notice
        title="No current games"
        message="Find a game to join or create a new one."
        icon={Inbox}
        actions={
          <>
            <div className="flex gap-2">
              <Button asChild>
                <Link to="/find-games">Find games</Link>
              </Button>
              <Button asChild variant="outline">
                <Link to="/create-game">Create a game</Link>
              </Button>
            </div>
            <Button asChild variant="link">
              <Link to="?view=finished">Show finished games</Link>
            </Button>
          </>
        }
      />
    );
  }

  const hasAttention = data.sections.some(section => section.key === "needs_attention");

  return (
    <div className="space-y-6">
      {!hasAttention && (
        <p className="flex items-center gap-2 text-sm text-muted-foreground">
          <CircleCheck className="size-4" />
          You're all caught up
        </p>
      )}
      {data.sections.map(section => (
        <section key={section.key} className="space-y-3">
          <h2 className="flex items-center gap-2 font-semibold">
            {section.key === "needs_attention" && (
              <span className="size-2 rounded-full bg-amber-500" />
            )}
            {sectionTitles[section.key]}
          </h2>
          {section.games.map(game => (
            <MyGameCard key={game.id} game={game} />
          ))}
        </section>
      ))}
    </div>
  );
};

const FinishedGames: React.FC = () => {
  const { data, fetchNextPage, hasNextPage, isFetchingNextPage } =
    useSuspenseInfiniteQuery({
      queryKey: [...getGamesMineFinishedListQueryKey(), "infinite"],
      queryFn: ({ pageParam }) => gamesMineFinishedList({ page: pageParam }),
      initialPageParam: 1,
      getNextPageParam: lastPage => {
        if (!lastPage.next) return undefined;
        const page = new URL(lastPage.next).searchParams.get("page");
        return page ? Number(page) : undefined;
      },
      staleTime: 0,
    });
  const sentinelRef = useInfiniteScroll(fetchNextPage, hasNextPage, isFetchingNextPage);
  const games = data.pages.flatMap(page => page.results);

  if (games.length === 0) {
    return (
      <Notice
        title="No finished games yet"
        message="Games you finish, leave or are eliminated from will appear here."
        icon={History}
      />
    );
  }

  return (
    <div className="space-y-3">
      {games.map(game => (
        <MyGameCard key={game.id} game={game} />
      ))}
      {isFetchingNextPage && (
        <div className="flex justify-center py-4">
          <Loader2 className="animate-spin" />
        </div>
      )}
      <div ref={sentinelRef} />
    </div>
  );
};

const MyGamesSkeleton: React.FC = () => (
  <div className="space-y-3">
    <Skeleton className="h-6 w-32" />
    {[0, 1, 2].map(index => (
      <div key={index} className="flex flex-col overflow-hidden rounded-xl border md:flex-row">
        <Skeleton className="h-40 rounded-none md:h-44 md:w-48" />
        <div className="flex flex-col gap-2 p-4 md:py-3">
          <Skeleton className="h-5 w-40" />
          <Skeleton className="h-4 w-28" />
        </div>
      </div>
    ))}
  </div>
);

const MyGamesSuspense: React.FC = () => {
  const view = useView();

  return (
    <ScreenContainer>
      <ScreenHeader title="My Games" actions={<ViewSelector />} />
      <QueryErrorBoundary key={view}>
        <Suspense fallback={<MyGamesSkeleton />}>
          {view === "finished" ? <FinishedGames /> : <CurrentGames />}
        </Suspense>
      </QueryErrorBoundary>
    </ScreenContainer>
  );
};

export { MyGamesSuspense as MyGames };
