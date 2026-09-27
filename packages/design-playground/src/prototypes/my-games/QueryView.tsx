import { Button } from "@/components/ui/button";
import {
  Empty,
  EmptyContent,
  EmptyDescription,
  EmptyHeader,
  EmptyMedia,
  EmptyTitle,
} from "@/components/ui/empty";
import { Input } from "@/components/ui/input";
import { ListSection } from "@/components/ui/list";
import { ScreenContainer } from "@/components/ui/screen-container";
import { HomeShell } from "@/components/HomeShell";
import { ScreenHeader } from "@/components/ScreenHeader";
import {
  myGamesDefault,
  myGamesMany,
  myGamesMustering,
} from "@/data/fixtures";
import { Inbox, Search, SearchX, X } from "lucide-react";
import { useState } from "react";
import type { Game } from "@/data/types";
import {
  CompactGameRow,
  gameNeedsAction,
  MusteringAlert,
  ResultCount,
  sortByAttention,
} from "./MyGameCard";

const presets = [
  { label: "Current", query: "-status:finished -sandbox:true" },
  { label: "Needs me", query: "needs:me" },
  { label: "Mustering", query: "status:mustering" },
  { label: "History", query: "status:finished" },
  { label: "Sandbox", query: "sandbox:true" },
];

const gamesForState = (state: string): Game[] => {
  if (state === "empty") return [];
  if (state === "many") return myGamesMany;
  if (state === "mustering" || state === "filtered-empty") {
    return myGamesMustering;
  }
  return myGamesDefault;
};

const initialQuery = (state: string) => {
  if (state === "mustering") return "status:mustering";
  if (state === "filtered-empty") return "status:finished sandbox:true";
  return "-status:finished -sandbox:true";
};

const isFinished = (game: Game) =>
  game.status === "completed" || game.status === "abandoned";

const gameMatchesToken = (game: Game, token: string) => {
  const excluded = token.startsWith("-");
  const value = excluded ? token.slice(1) : token;
  let matches = true;

  if (value === "needs:me") matches = gameNeedsAction(game);
  else if (value === "status:finished") matches = isFinished(game);
  else if (value === "status:staging") matches = game.status === "pending";
  else if (value.startsWith("status:")) matches = game.status === value.slice(7);
  else if (value === "sandbox:true") matches = game.sandbox === true;
  else {
    matches = game.name.toLowerCase().includes(value.toLowerCase());
  }

  return excluded ? !matches : matches;
};

const matchesQuery = (game: Game, query: string) => {
  const tokens = query.trim().split(/\s+/).filter(Boolean);
  return tokens.every(token => gameMatchesToken(game, token));
};

const QueryView: React.FC<{ state: string }> = ({ state }) => {
  const games = gamesForState(state);
  const [query, setQuery] = useState(() => initialQuery(state));
  const visibleGames = sortByAttention(
    games.filter(game => matchesQuery(game, query))
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
                Create or join a game before building a view.
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
            <div className="space-y-2 rounded-lg border bg-card p-3">
              <label htmlFor="games-query" className="text-sm font-medium">
                Filter expression
              </label>
              <div className="relative">
                <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  id="games-query"
                  value={query}
                  onChange={event => setQuery(event.target.value)}
                  className="pl-9 pr-9 font-mono text-sm"
                  aria-describedby="games-query-help"
                />
                {query && (
                  <button
                    type="button"
                    aria-label="Clear filter"
                    onClick={() => setQuery("")}
                    className="absolute right-2 top-1/2 flex size-7 -translate-y-1/2 items-center justify-center rounded-md text-muted-foreground hover:bg-muted hover:text-foreground"
                  >
                    <X className="size-4" />
                  </button>
                )}
              </div>
              <p id="games-query-help" className="text-xs text-muted-foreground">
                Try status:mustering, needs:me, sandbox:true, or prefix a term with -.
              </p>
              <div className="-mx-1 overflow-x-auto px-1 pb-1">
                <div className="flex w-max gap-2">
                  {presets.map(preset => (
                    <Button
                      key={preset.label}
                      size="sm"
                      variant={query === preset.query ? "secondary" : "ghost"}
                      onClick={() => setQuery(preset.query)}
                      className="rounded-full"
                    >
                      {preset.label}
                    </Button>
                  ))}
                </div>
              </div>
            </div>

            <div className="flex items-center justify-between gap-3">
              <h2 className="font-semibold">Results</h2>
              <ResultCount count={visibleGames.length} />
            </div>
            {visibleGames.length === 0 ? (
              <Empty className="border">
                <EmptyHeader>
                  <EmptyMedia variant="icon">
                    <SearchX />
                  </EmptyMedia>
                  <EmptyTitle>No games match that expression</EmptyTitle>
                  <EmptyDescription>
                    Change or clear the expression. No games have been removed.
                  </EmptyDescription>
                </EmptyHeader>
                <EmptyContent>
                  <Button variant="outline" onClick={() => setQuery("")}>
                    Clear expression
                  </Button>
                </EmptyContent>
              </Empty>
            ) : (
              <ListSection>
                {visibleGames.map(game => (
                  <li
                    key={game.id}
                    className="border-b border-border last:border-b-0"
                  >
                    <CompactGameRow game={game} />
                  </li>
                ))}
              </ListSection>
            )}
          </div>
        )}
      </ScreenContainer>
    </HomeShell>
  );
};

export { QueryView };
