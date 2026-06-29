import React, { Suspense } from "react";
import { GameCard } from "@/components/GameCard";
import { MapView } from "@/components/MapView";
import { QueryErrorBoundary } from "@/components/QueryErrorBoundary";
import { ScreenContainer } from "@/components/ui/screen-container";
import { ScreenHeader } from "@/components/ui/screen-header";
import { gameFixtures, allVariants } from "@/mocks/fixtures";
import type { GameList } from "@/api/generated/endpoints";

const f = gameFixtures;

const active = f.activeGameMovement.game;
const pendingSome = f.pendingGameSomePlayers.game;

const variant = allVariants[Math.floor(Math.random() * allVariants.length)];

const nationName = (i: number) =>
  variant.nations[i % variant.nations.length].name;

const withVariantNations = (game: GameList): GameList => ({
  ...game,
  members: game.members.map((m, i) => ({
    ...m,
    nation: m.nation ? nationName(i) : m.nation,
  })),
  victory: game.victory
    ? {
        ...game.victory,
        members: game.victory.members.map((m, i) => ({
          ...m,
          nation: nationName(i),
        })),
      }
    : game.victory,
});

interface Scenario {
  label: string;
  game: GameList;
}

const myGamesScenarios: Scenario[] = [
  { label: "Orders required", game: { ...active, orderStatus: "orders_required", memberStatus: [] } },
  { label: "Orders submitted", game: { ...active, orderStatus: "orders_submitted", memberStatus: [] } },
  { label: "Orders not confirmed", game: { ...active, orderStatus: "orders_not_confirmed", memberStatus: [] } },
  { label: "No orders required", game: { ...active, orderStatus: "no_orders_required", memberStatus: [] } },
  { label: "NMR", game: { ...active, orderStatus: "orders_required", memberStatus: ["nmr"] } },
  { label: "Civil disorder", game: { ...active, orderStatus: "no_orders_required", memberStatus: ["civil_disorder"] } },
  { label: "Gunboat (no press)", game: { ...active, pressType: "no_press", orderStatus: "orders_required" } },
  { label: "Paused", game: { ...active, isPaused: true, orderStatus: "orders_required" } },
  { label: "Unread messages", game: { ...active, totalUnreadMessageCount: 12 } },
  { label: "Retreat phase", game: f.activeGameRetreat.game },
  { label: "Build phase", game: f.activeGameBuild.game },
  { label: "Draw proposal", game: f.activeGameDrawProposal.game },
  { label: "Non-playing Game Master", game: f.gameMasterGame.game },
  { label: "Sandbox", game: { ...active, sandbox: true, orderStatus: "orders_required" } },
];

const pendingScenarios: Scenario[] = [
  { label: "No players joined", game: f.pendingGameNoPlayers.game },
  { label: "Some players joined", game: pendingSome },
  { label: "Almost full", game: f.pendingGameAlmostFull.game },
  { label: "Private + non-playing GM", game: { ...pendingSome, private: true, gameMaster: { userId: 9999, name: "Zara", picture: null } } },
];

const finishedScenarios: Scenario[] = [
  { label: "Solo victory", game: f.finishedGameSolo.game },
  { label: "Draw", game: f.finishedGameDraw.game },
  { label: "Solo victory + unread", game: { ...f.finishedGameSolo.game, totalUnreadMessageCount: 5 } },
  { label: "Solo victory + civil disorder", game: { ...f.finishedGameSolo.game, memberStatus: ["civil_disorder"] } },
  { label: "Abandoned", game: { ...f.finishedGameSolo.game, status: "abandoned", victory: null } },
];

const ScenarioCard: React.FC<Scenario> = ({ label, game }) => (
  <div className="space-y-1">
    <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
      {label}
    </p>
    <GameCard
      game={withVariantNations(game)}
      variant={variant}
      map={
        <MapView
          mode="static"
          variant={variant}
          phase={variant.templatePhase}
          cover
          className="w-full h-full"
        />
      }
    />
  </div>
);

const Section: React.FC<{ title: string; scenarios: Scenario[] }> = ({
  title,
  scenarios,
}) => (
  <div className="space-y-4">
    <h2 className="text-lg font-semibold border-b pb-1">{title}</h2>
    {scenarios.map(s => (
      <ScenarioCard key={s.label} {...s} />
    ))}
  </div>
);

const CardGallery: React.FC = () => (
  <ScreenContainer>
    <ScreenHeader title={`Card Gallery — ${variant.name}`} />
    <QueryErrorBoundary>
      <Suspense fallback={<div />}>
        <div className="space-y-10 pb-16">
          <Section title="My Games — active" scenarios={myGamesScenarios} />
          <Section title="Pending" scenarios={pendingScenarios} />
          <Section title="Finished" scenarios={finishedScenarios} />
        </div>
      </Suspense>
    </QueryErrorBoundary>
  </ScreenContainer>
);

export { CardGallery };
export default CardGallery;
