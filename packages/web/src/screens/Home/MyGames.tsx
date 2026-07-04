import React, { Fragment, Suspense, useState } from "react";
import { Link } from "react-router";

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ScreenHeader } from "@/components/ui/screen-header";
import { ScreenContainer } from "@/components/ui/screen-container";
import { GameCard } from "@/components/GameCard";
import { MapView } from "@/components/MapView";
import { Notice } from "@/components/Notice";
import { Button } from "@/components/ui/button";
import { Inbox, Loader2 } from "lucide-react";
import { QueryErrorBoundary } from "@/components/QueryErrorBoundary";
import type { GameList } from "@/api/generated/endpoints";
import { useGamesListInfinite } from "@/hooks/useGamesListInfinite";
import { useGameVariant } from "@/hooks/useGameVariant";
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

interface GameTabContentProps {
  statusFilter: string;
  emptyTitle: string;
  status: StatusValue;
  ordering?: string;
}

const MyGameCard: React.FC<{ game: GameList }> = ({ game }) => {
  const variant = useGameVariant(game);
  if (!variant) return null;

  return (
    <GameCard
      game={game}
      variant={variant}
      map={
        <MapView
          mode="static"
          variant={variant}
          phase={game.currentPhase ?? variant.templatePhase}
          cover
          className="w-full h-full"
        />
      }
    />
  );
};

const GameTabContent: React.FC<GameTabContentProps> = ({
  statusFilter,
  emptyTitle,
  status,
  ordering,
}) => {
  const { data, fetchNextPage, hasNextPage, isFetchingNextPage } =
    useGamesListInfinite({ mine: true, status: statusFilter, ordering });

  const games = data.pages.flatMap(page => page.results);

  const sentinelRef = useInfiniteScroll(
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage
  );

  if (games.length === 0) {
    const { message, actions } = getEmptyStateConfig(status);
    return (
      <Notice title={emptyTitle} message={message} icon={Inbox} actions={actions} />
    );
  }

  const firstEliminatedIndex =
    status === "active"
      ? games.findIndex(game => !game.sandbox && game.members.find(m => m.isCurrentUser)?.eliminated)
      : -1;

  return (
    <div className="space-y-4">
      {games.map((game, index) => (
        <Fragment key={game.id}>
          {index === firstEliminatedIndex && (
            <h3 className="text-sm font-semibold pt-2">Eliminated</h3>
          )}
          <MyGameCard game={game} />
        </Fragment>
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
