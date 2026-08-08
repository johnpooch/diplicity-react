import { Badge } from "@/components/ui/badge";
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
import { GameCard } from "@/components/GameCard";
import { HomeShell } from "@/components/HomeShell";
import { ScreenHeader } from "@/components/ScreenHeader";
import { games, manyGames } from "@/data/fixtures";
import { Inbox } from "lucide-react";
import type { Game } from "@/data/types";

const groups = [
  {
    key: "needs-you",
    title: "Needs you",
    description: "Deadline approaching and orders not in",
    match: (game: Game) =>
      game.status === "active" && game.orderStatus === "orders_required",
  },
  {
    key: "waiting",
    title: "Waiting on others",
    description: "Your orders are in",
    match: (game: Game) =>
      game.status === "active" && game.orderStatus !== "orders_required",
  },
  {
    key: "staging",
    title: "Staging",
    description: "Not started yet",
    match: (game: Game) => game.status === "pending",
  },
  {
    key: "finished",
    title: "Finished",
    description: "",
    match: (game: Game) => game.status === "completed",
  },
];

const gamesForState = (state: string): Game[] => {
  if (state === "empty") return [];
  if (state === "many") return manyGames;
  return games;
};

const GroupedByPhase: React.FC<{ state: string }> = ({ state }) => {
  const list = gamesForState(state);

  return (
    <HomeShell activeNavItem="My Games">
      <ScreenContainer>
        <ScreenHeader title="My Games" />
        {list.length === 0 ? (
          <Empty>
            <EmptyHeader>
              <EmptyMedia variant="icon">
                <Inbox />
              </EmptyMedia>
              <EmptyTitle>No games yet</EmptyTitle>
              <EmptyDescription>
                Games you join will be grouped here by what they need from you.
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
          <div className="flex flex-col gap-6">
            {groups.map(group => {
              const groupGames = list.filter(group.match);
              if (groupGames.length === 0) return null;

              return (
                <section key={group.key} className="flex flex-col gap-2">
                  <div className="flex items-baseline gap-2">
                    <h2 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
                      {group.title}
                    </h2>
                    <Badge variant="secondary">{groupGames.length}</Badge>
                    {group.description && (
                      <span className="hidden text-xs text-muted-foreground sm:inline">
                        {group.description}
                      </span>
                    )}
                  </div>
                  <div className="flex flex-col gap-2">
                    {groupGames.map(game => (
                      <GameCard key={game.id} game={game} />
                    ))}
                  </div>
                </section>
              );
            })}
          </div>
        )}
      </ScreenContainer>
    </HomeShell>
  );
};

export { GroupedByPhase };
