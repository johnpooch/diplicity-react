import React, { Suspense, useState } from "react";

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ScreenHeader } from "@/components/ui/screen-header";
import { ScreenContainer } from "@/components/ui/screen-container";
import { GameCard } from "@/components/GameCard";
import { Notice } from "@/components/Notice";
import { Inbox, Loader2 } from "lucide-react";
import { QueryErrorBoundary } from "@/components/QueryErrorBoundary";
import { useVariantsListSuspense } from "@/api/generated/endpoints";
import { useGamesListInfinite } from "@/hooks/useGamesListInfinite";
import { useInfiniteScroll } from "@/hooks/useInfiniteScroll";

const statuses = [
  { value: "pending", label: "Staging", statusFilter: "pending" },
  { value: "active", label: "Started", statusFilter: "active" },
  {
    value: "completed",
    label: "Finished",
    statusFilter: "completed,abandoned",
  },
] as const;

type StatusValue = (typeof statuses)[number]["value"];

const getStatusMessage = (status: StatusValue) => {
  switch (status) {
    case "pending":
      return "You are not a member of any staging games. Go to Find Games to join a game.";
    case "active":
      return "You are not a member of any started games. When you join a game, it will be in a pending state until the required number of players have joined.";
    case "completed":
      return "You have not finished any games. When a game ends by victory, draw, or abandonment, it will appear here.";
  }
};

interface GameTabContentProps {
  statusFilter: string;
  emptyTitle: string;
  emptyMessage: string;
}

const GameTabContent: React.FC<GameTabContentProps> = ({
  statusFilter,
  emptyTitle,
  emptyMessage,
}) => {
  const { data, fetchNextPage, hasNextPage, isFetchingNextPage } =
    useGamesListInfinite({ mine: true, status: statusFilter });
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
    return <Notice title={emptyTitle} message={emptyMessage} icon={Inbox} />;
  }

  return (
    <div className="space-y-4">
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

        {statuses.map(status => (
          <TabsContent key={status.value} value={status.value}>
            <QueryErrorBoundary>
              <Suspense fallback={<div></div>}>
                <GameTabContent
                  statusFilter={status.statusFilter}
                  emptyTitle={`No ${status.label.toLowerCase()} games`}
                  emptyMessage={getStatusMessage(status.value)}
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
      <ScreenHeader title="My Games" showUserAvatar />
      <MyGames />
    </ScreenContainer>
  );
};

export { MyGamesSuspense as MyGames };
