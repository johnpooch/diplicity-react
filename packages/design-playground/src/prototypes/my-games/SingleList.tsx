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

const gamesForState = (state: string): Game[] => {
  if (state === "empty") return [];
  if (state === "many") return manyGames;
  return games;
};

const SingleList: React.FC<{ state: string }> = ({ state }) => {
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
                Games you join will appear here, newest deadline first.
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
          <div className="flex flex-col gap-2">
            {list.map(game => (
              <GameCard key={game.id} game={game} />
            ))}
          </div>
        )}
      </ScreenContainer>
    </HomeShell>
  );
};

export { SingleList };
