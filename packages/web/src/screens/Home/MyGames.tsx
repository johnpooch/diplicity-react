import React, { Suspense, useState } from "react";

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ScreenHeader } from "@/components/ui/screen-header";
import { ScreenContainer } from "@/components/ui/screen-container";
import { GameCard } from "@/components/GameCard";
import { Notice } from "@/components/Notice";
import { Inbox } from "lucide-react";
import { QueryErrorBoundary } from "@/components/QueryErrorBoundary";
import {
  GameList,
  useGamesListSuspense,
  useVariantsListSuspense,
} from "@/api/generated/endpoints";

const statuses = [
  { value: "pending", label: "Staging" },
  { value: "active", label: "Started" },
  { value: "completed", label: "Finished" },
] as const;

type Status = (typeof statuses)[number]["value"];

const statusPriority: readonly Status[] = ["active", "pending", "completed"];

const getStatusMessage = (status: Status) => {
  switch (status) {
    case "pending":
      return "You are not a member of any staging games. Go to Find Games to join a game.";
    case "active":
      return "You are not a member of any started games. When you join a game, it will be in a pending state until the required number of players have joined.";
    case "completed":
      return "You have not finished any games. When a game is finished, it will appear here.";
  }
};

const MyGames: React.FC = () => {
  const { data: games } = useGamesListSuspense({ mine: true });
  const { data: variants } = useVariantsListSuspense();

  const [selectedStatus, setSelectedStatus] = useState<Status>(() => {
    const firstStatusWithGames = statusPriority.find(status =>
      games.some(game => game.status === status)
    );
    return firstStatusWithGames ?? "active";
  });

  const getVariant = (game: GameList) => {
    const variant = variants.find(v => v.id === game.variantId);
    if (!variant) {
      throw new Error(`Variant not found for game ${game.id}`);
    }
    return variant;
  };

  return (
    <div className="flex flex-col items-center gap-4">
      <Tabs
        value={selectedStatus}
        onValueChange={value => setSelectedStatus(value as Status)}
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

        {statuses.map(status => {
          const filteredGames = games?.filter(
            game => game.status === status.value
          );
          return (
            <TabsContent key={status.value} value={status.value}>
              <div className="space-y-4">
                {filteredGames && filteredGames.length > 0 ? (
                  filteredGames.map(game => (
                    <GameCard
                      key={game.id}
                      game={game}
                      variant={getVariant(game)}
                      phaseId={game.phases[0]}
                      map={<div />}
                    />
                  ))
                ) : (
                  <Notice
                    title={`No ${status.label.toLowerCase()} games`}
                    message={getStatusMessage(status.value)}
                    icon={Inbox}
                  />
                )}
              </div>
            </TabsContent>
          );
        })}
      </Tabs>
    </div>
  );
};

const MyGamesSuspense: React.FC = () => {
  return (
    <ScreenContainer>
      <ScreenHeader title="My Games" />
      <QueryErrorBoundary>
        <Suspense fallback={<div></div>}>
          <MyGames />
        </Suspense>
      </QueryErrorBoundary>
    </ScreenContainer>
  );
};

export { MyGamesSuspense as MyGames };
