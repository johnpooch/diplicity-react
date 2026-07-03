import React, { Suspense, useState } from "react";
import { Link } from "react-router";

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ScreenHeader } from "@/components/ui/screen-header";
import { ScreenContainer } from "@/components/ui/screen-container";
import { GameCard } from "@/components/GameCard";
import { MapView } from "@/components/MapView";
import { Notice } from "@/components/Notice";
import { Button } from "@/components/ui/button";
import { AlertTriangle, Inbox, Loader2, Skull, UserX } from "lucide-react";
import { QueryErrorBoundary } from "@/components/QueryErrorBoundary";
import { useVariantsListSuspense } from "@/api/generated/endpoints";
import type { GameList } from "@/api/generated/endpoints";
import { useGamesListInfinite } from "@/hooks/useGamesListInfinite";
import { useInfiniteScroll } from "@/hooks/useInfiniteScroll";

const statuses = [
  { value: "pending", label: "Staging", statusFilter: "pending", ordering: undefined },
  { value: "active", label: "Started", statusFilter: "active", ordering: "deadline" },
  {
    value: "completed",
    label: "Finished",
    statusFilter: "completed,abandoned",
    ordering: undefined,
  },
] as const;

type StatusValue = (typeof statuses)[number]["value"];

interface EmptyStateConfig {
  message: string;
  actions: React.ReactNode;
}

const getEmptyStateConfig = (status: StatusValue): EmptyStateConfig => {
  switch (status) {
    case "pending":
      return {
        message:
          "Games you've joined that are waiting for more players will appear here. Create a new game or find one to join!",
        actions: (
          <div className="flex gap-2">
            <Button asChild>
              <Link to="/create-game">Create a game</Link>
            </Button>
            <Button asChild variant="outline">
              <Link to="/find-games">Find a game</Link>
            </Button>
          </div>
        ),
      };
    case "active":
      return {
        message:
          "Your active games will appear here. Ready to play? Create a new game, try a sandbox to practice, or find an open game to join.",
        actions: (
          <div className="flex gap-2">
            <Button asChild>
              <Link to="/create-game">Create a game</Link>
            </Button>
            <Button asChild variant="outline">
              <Link to="/find-games">Find a game</Link>
            </Button>
          </div>
        ),
      };
    case "completed":
      return {
        message:
          "Completed games will appear here. When a game ends by victory, draw, or abandonment, you'll find it in this list.",
        actions: (
          <div className="flex gap-2">
            <Button asChild>
              <Link to="/create-game">Create a game</Link>
            </Button>
          </div>
        ),
      };
  }
};

const ACTIVE_LANES = [
  {
    key: "civil_disorder",
    label: "Civil Disorder — submit to rejoin",
    icon: UserX,
    className: "text-red-600",
  },
  {
    key: "nmr",
    label: "No moves received last phase",
    icon: AlertTriangle,
    className: "text-amber-600",
  },
  { key: "orders_required", label: "Needs your orders", icon: null, className: "" },
  {
    key: "waiting",
    label: "Waiting on others",
    icon: null,
    className: "text-muted-foreground",
  },
  { key: "eliminated", label: "Eliminated", icon: Skull, className: "text-muted-foreground" },
] as const;

const laneForGame = (game: GameList): string => {
  const member = game.members.find(m => m.isCurrentUser);
  if (!game.sandbox && member?.eliminated) return "eliminated";
  const status = game.memberStatus ?? [];
  if (status.includes("civil_disorder")) return "civil_disorder";
  if (status.includes("nmr")) return "nmr";
  if (game.orderStatus === "orders_required") return "orders_required";
  return "waiting";
};

interface GameTabContentProps {
  statusFilter: string;
  emptyTitle: string;
  status: StatusValue;
  ordering?: string;
}

const GameTabContent: React.FC<GameTabContentProps> = ({
  statusFilter,
  emptyTitle,
  status,
  ordering,
}) => {
  const { data, fetchNextPage, hasNextPage, isFetchingNextPage } =
    useGamesListInfinite({ mine: true, status: statusFilter, ordering });
  const { data: variants } = useVariantsListSuspense();

  const games = data.pages.flatMap(page => page.results);

  const sentinelRef = useInfiniteScroll(
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage
  );

  const variantMap = new Map(variants.map(v => [v.id, v]));
  const knownGames = games.filter(game => variantMap.has(game.variantId));

  if (knownGames.length === 0) {
    const { message, actions } = getEmptyStateConfig(status);
    return (
      <Notice title={emptyTitle} message={message} icon={Inbox} actions={actions} />
    );
  }

  const renderCard = (game: GameList, mode: "default" | "active") => (
    <GameCard
      key={game.id}
      game={game}
      mode={mode}
      variant={variantMap.get(game.variantId)!}
      map={
        <MapView
          mode="static"
          variant={variantMap.get(game.variantId)!}
          phase={game.currentPhase ?? variantMap.get(game.variantId)!.templatePhase}
          cover
          className="w-full h-full"
        />
      }
    />
  );

  const loadMore = (
    <>
      {isFetchingNextPage && (
        <div className="flex justify-center py-4">
          <Loader2 className="animate-spin" />
        </div>
      )}
      <div ref={sentinelRef} />
    </>
  );

  if (status === "active") {
    return (
      <div className="space-y-4">
        {ACTIVE_LANES.map(lane => {
          const laneGames = knownGames.filter(game => laneForGame(game) === lane.key);
          if (laneGames.length === 0) return null;
          const Icon = lane.icon;
          return (
            <div key={lane.key} className="space-y-4">
              <div className="flex items-center gap-2 pt-2">
                {Icon && <Icon className={`size-4 ${lane.className}`} />}
                <h3 className={`text-sm font-semibold ${lane.className}`}>
                  {lane.label}
                </h3>
                <span className="inline-flex items-center justify-center min-w-5 h-5 px-1.5 rounded-full bg-muted text-xs font-medium">
                  {laneGames.length}
                </span>
              </div>
              {laneGames.map(game => renderCard(game, "active"))}
            </div>
          );
        })}
        {loadMore}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {knownGames.map(game => renderCard(game, "default"))}
      {loadMore}
    </div>
  );
};

const MyGames: React.FC = () => {
  const [selectedStatus, setSelectedStatus] = useState<StatusValue>("active");

  return (
    <div className="flex flex-col items-center gap-4">
      <Tabs
        value={selectedStatus}
        onValueChange={value => setSelectedStatus(value as StatusValue)}
        className="w-full"
      >
        <TabsList className="w-full">
          {statuses.map(status => (
            <TabsTrigger
              key={status.value}
              value={status.value}
              className="flex-1"
            >
              {status.label}
            </TabsTrigger>
          ))}
        </TabsList>

        {statuses.map(s => (
          <TabsContent key={s.value} value={s.value}>
            <QueryErrorBoundary>
              <Suspense fallback={<div></div>}>
                <GameTabContent
                  statusFilter={s.statusFilter}
                  emptyTitle={`No ${s.label.toLowerCase()} games`}
                  status={s.value}
                  ordering={s.ordering}
                />
              </Suspense>
            </QueryErrorBoundary>
          </TabsContent>
        ))}
      </Tabs>
    </div>
  );
};

const MyGamesSuspense: React.FC = () => {
  return (
    <ScreenContainer>
      <ScreenHeader title="My Games" />
      <MyGames />
    </ScreenContainer>
  );
};

export { MyGamesSuspense as MyGames };
