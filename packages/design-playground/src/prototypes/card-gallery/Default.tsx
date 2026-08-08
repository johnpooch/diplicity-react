import { ScreenContainer } from "@/components/ui/screen-container";
import { GameCard } from "@/components/GameCard";
import { HomeShell } from "@/components/HomeShell";
import { ScreenHeader } from "@/components/ScreenHeader";
import {
  activeGame,
  activeGameBuild,
  activeGameRetreat,
  activeGameSubmitted,
  completedGame,
  pendingGame,
  pendingGameAlmostFull,
} from "@/data/fixtures";
import type { Game } from "@/data/types";

interface Scenario {
  label: string;
  game: Game;
}

const scenarios: Scenario[] = [
  { label: "Orders required", game: activeGame },
  { label: "Orders submitted", game: activeGameSubmitted },
  { label: "Orders confirmed", game: activeGameBuild },
  { label: "No orders required (retreat)", game: activeGameRetreat },
  { label: "Deadline imminent", game: { ...activeGame, phase: { ...activeGame.phase, deadline: "in 8 minutes" } } },
  { label: "Unread messages", game: { ...activeGame, unreadCount: 24 } },
  { label: "No unread messages", game: { ...activeGame, unreadCount: 0 } },
  { label: "Private game", game: { ...activeGame, isPrivate: true } },
  { label: "Long name", game: { ...activeGame, name: "The Extremely Long Game Name That Someone Will Definitely Type One Day" } },
  { label: "Staging, few players", game: { ...pendingGame, members: pendingGame.members.slice(0, 2) } },
  { label: "Staging, almost full", game: pendingGameAlmostFull },
  { label: "Finished, solo victory", game: completedGame },
];

const CardGallery: React.FC = () => {
  return (
    <HomeShell activeNavItem="My Games">
      <ScreenContainer>
        <ScreenHeader title="Game card gallery" />
        <div className="flex flex-col gap-6">
          {scenarios.map(scenario => (
            <div key={scenario.label} className="flex flex-col gap-2">
              <p className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
                {scenario.label}
              </p>
              <GameCard game={scenario.game} />
            </div>
          ))}
        </div>
      </ScreenContainer>
    </HomeShell>
  );
};

export { CardGallery };
