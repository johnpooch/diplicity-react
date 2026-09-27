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
import { ListSection } from "@/components/ui/list";
import { ScreenContainer } from "@/components/ui/screen-container";
import { HomeShell } from "@/components/HomeShell";
import { ScreenHeader } from "@/components/ScreenHeader";
import {
  myGamesDefault,
  myGamesMany,
  myGamesMustering,
} from "@/data/fixtures";
import { ArrowRight, Inbox, Sparkles } from "lucide-react";
import type { Game } from "@/data/types";
import {
  CompactGameRow,
  gameNeedsAction,
  MyGameCard,
  sortByAttention,
} from "./MyGameCard";

const gamesForState = (state: string): Game[] => {
  if (state === "empty") return [];
  if (state === "many") return myGamesMany;
  if (state === "mustering") return myGamesMustering;
  return myGamesDefault;
};

const ActionQueue: React.FC<{ state: string }> = ({ state }) => {
  const games = sortByAttention(gamesForState(state));
  const actionable = games.filter(gameNeedsAction);
  const next = actionable[0];
  const later = games.filter(game => game.id !== next?.id);

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
                Join or create a game and your next action will appear here.
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
          <div className="space-y-5">
            {next ? (
              <section className="space-y-2" aria-labelledby="next-action-heading">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <div className="flex items-center gap-2">
                      <Sparkles className="size-4 text-primary" />
                      <h2 id="next-action-heading" className="font-semibold">
                        Do this next
                      </h2>
                    </div>
                    <p className="text-sm text-muted-foreground">
                      Most urgent of {actionable.length} actions
                    </p>
                  </div>
                  <Badge variant="secondary">{actionable.length} need you</Badge>
                </div>
                <MyGameCard game={next} prominent />
              </section>
            ) : (
              <div className="rounded-lg border bg-muted/40 p-4">
                <p className="font-medium">You are caught up</p>
                <p className="text-sm text-muted-foreground">
                  Nothing needs you right now. Your games are still below.
                </p>
              </div>
            )}

            {later.length > 0 && (
              <ListSection
                header={
                  <div className="flex items-center justify-between gap-2">
                    <div>
                      <h2 className="text-sm font-medium">Coming up</h2>
                      <p className="text-xs text-muted-foreground">
                        Urgent first, sandbox and history last
                      </p>
                    </div>
                    <Button size="sm" variant="ghost" className="gap-1">
                      Filters
                      <ArrowRight className="size-3.5" />
                    </Button>
                  </div>
                }
              >
                {later.map(game => (
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

export { ActionQueue };
