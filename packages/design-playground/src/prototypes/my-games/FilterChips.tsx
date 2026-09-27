import { Button } from "@/components/ui/button";
import {
  Empty,
  EmptyContent,
  EmptyDescription,
  EmptyHeader,
  EmptyMedia,
  EmptyTitle,
} from "@/components/ui/empty";
import { ScreenContainer } from "@/components/ui/screen-container";
import { HomeShell } from "@/components/HomeShell";
import { ScreenHeader } from "@/components/ScreenHeader";
import {
  myGamesDefault,
  myGamesMany,
  myGamesMustering,
} from "@/data/fixtures";
import { Inbox, SearchX } from "lucide-react";
import { useState } from "react";
import type { Game } from "@/data/types";
import {
  gameNeedsAction,
  MusteringAlert,
  MyGameCard,
  ResultCount,
  sortByAttention,
} from "./MyGameCard";

type FilterKey =
  | "current"
  | "needs-you"
  | "mustering"
  | "active"
  | "pending"
  | "finished"
  | "sandbox";

const filters: Array<{ key: FilterKey; label: string }> = [
  { key: "current", label: "Current" },
  { key: "needs-you", label: "Needs you" },
  { key: "mustering", label: "Mustering" },
  { key: "active", label: "Active" },
  { key: "pending", label: "Staging" },
  { key: "finished", label: "Finished" },
  { key: "sandbox", label: "Practice" },
];

const matchesFilter = (game: Game, filter: FilterKey) => {
  if (filter === "current") {
    return game.status !== "completed" && game.status !== "abandoned";
  }
  if (filter === "needs-you") return gameNeedsAction(game);
  if (filter === "finished") {
    return game.status === "completed" || game.status === "abandoned";
  }
  if (filter === "sandbox") return game.sandbox === true;
  return game.status === filter;
};

const gamesForState = (state: string): Game[] => {
  if (state === "empty") return [];
  if (state === "many") return myGamesMany;
  if (state === "mustering" || state === "filtered-empty") {
    return myGamesMustering;
  }
  return myGamesDefault;
};

const initialFilter = (state: string): FilterKey => {
  if (state === "mustering") return "mustering";
  if (state === "filtered-empty") return "finished";
  return "current";
};

const FilterChips: React.FC<{ state: string }> = ({ state }) => {
  const games = gamesForState(state);
  const [filter, setFilter] = useState<FilterKey>(() => initialFilter(state));
  const visibleGames = sortByAttention(
    games.filter(game => matchesFilter(game, filter))
  );

  return (
    <HomeShell activeNavItem="My Games">
      <ScreenContainer>
        <ScreenHeader title="My Games" />
        {games.length === 0 ? (
          <Empty>
            <EmptyHeader>
              <EmptyMedia variant="icon">
                <Inbox />
              </EmptyMedia>
              <EmptyTitle>No games yet</EmptyTitle>
              <EmptyDescription>
                Games you create or join will appear here.
              </EmptyDescription>
            </EmptyHeader>
            <EmptyContent>
              <div className="flex gap-2">
                <Button>Create a game</Button>
                <Button variant="outline">Find a game</Button>
              </div>
            </EmptyContent>
          </Empty>
        ) : (
          <div className="space-y-4">
            <MusteringAlert games={games} />
            <div className="-mx-2 overflow-x-auto px-2 pb-1" aria-label="Filter games">
              <div className="flex w-max gap-2">
                {filters.map(option => {
                  const count = games.filter(game => matchesFilter(game, option.key)).length;
                  return (
                    <Button
                      key={option.key}
                      size="sm"
                      variant={filter === option.key ? "default" : "outline"}
                      aria-pressed={filter === option.key}
                      onClick={() => setFilter(option.key)}
                      className="rounded-full"
                    >
                      {option.label}
                      <span aria-hidden="true" className="opacity-70">
                        {count}
                      </span>
                    </Button>
                  );
                })}
              </div>
            </div>
            <div className="flex items-center justify-between gap-3">
              <h2 className="font-semibold">
                {filters.find(option => option.key === filter)?.label}
              </h2>
              <ResultCount count={visibleGames.length} />
            </div>
            {visibleGames.length === 0 ? (
              <Empty className="border">
                <EmptyHeader>
                  <EmptyMedia variant="icon">
                    <SearchX />
                  </EmptyMedia>
                  <EmptyTitle>No games match this filter</EmptyTitle>
                  <EmptyDescription>
                    Your games are still here. Choose another filter to see them.
                  </EmptyDescription>
                </EmptyHeader>
                <EmptyContent>
                  <Button variant="outline" onClick={() => setFilter("current")}>
                    Show current games
                  </Button>
                </EmptyContent>
              </Empty>
            ) : (
              <div className="grid gap-3 sm:grid-cols-2">
                {visibleGames.map(game => (
                  <MyGameCard key={game.id} game={game} />
                ))}
              </div>
            )}
          </div>
        )}
      </ScreenContainer>
    </HomeShell>
  );
};

export { FilterChips };
