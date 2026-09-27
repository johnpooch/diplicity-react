import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import {
  Empty,
  EmptyContent,
  EmptyDescription,
  EmptyHeader,
  EmptyMedia,
  EmptyTitle,
} from "@/components/ui/empty";
import { ScreenContainer } from "@/components/ui/screen-container";
import {
  Sheet,
  SheetClose,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import { HomeShell } from "@/components/HomeShell";
import { ScreenHeader } from "@/components/ScreenHeader";
import { StaticMap } from "@/components/StaticMap";
import { myGamesAllStates, myGamesMany } from "@/data/fixtures";
import { cn } from "@/lib/utils";
import {
  AlertCircle,
  Check,
  CheckCircle2,
  CircleDashed,
  Clock3,
  Filter,
  Handshake,
  Inbox,
  Mail,
  Pause,
  SearchX,
  ShieldAlert,
  Skull,
  Trophy,
  UserRound,
  Users,
} from "lucide-react";
import { useState } from "react";
import type { Game } from "@/data/types";

type ViewKey =
  | "current"
  | "needs-you"
  | "mustering"
  | "active"
  | "pending"
  | "finished"
  | "sandbox";

interface ViewOption {
  key: ViewKey;
  label: string;
}

interface GameSection {
  key: string;
  title: string;
  attention?: boolean;
  matches: (game: Game) => boolean;
  sort: (first: Game, second: Game) => number;
}

const views: ViewOption[] = [
  { key: "current", label: "Current" },
  { key: "needs-you", label: "Needs attention" },
  { key: "mustering", label: "Mustering" },
  { key: "active", label: "Active" },
  { key: "pending", label: "Pending" },
  { key: "finished", label: "Finished" },
  { key: "sandbox", label: "Sandbox" },
];

const byDeadline = (first: Game, second: Game) =>
  (first.deadlineMinutes ?? Number.POSITIVE_INFINITY) -
    (second.deadlineMinutes ?? Number.POSITIVE_INFINITY) ||
  first.name.localeCompare(second.name);

const byPendingFill = (first: Game, second: Game) =>
  second.members.length - first.members.length || first.name.localeCompare(second.name);

const byActiveState = (first: Game, second: Game) => {
  const disposition = (game: Game) => {
    if (game.userEliminated) return 4;
    if (game.isPaused) return 3;
    if (game.replaceableSeat || game.otherPlayerInCivilDisorder) return 2;
    if (game.unreadCount > 0) return 0;
    return 1;
  };
  return disposition(first) - disposition(second) || byDeadline(first, second);
};

const needsAttention = (game: Game) => {
  if (game.userInCivilDisorder) return false;
  if (game.status === "mustering") {
    return game.musteringStatus === "unconfirmed";
  }
  if (game.status !== "active" || game.sandbox) return false;
  return (
    game.attention === "missed_deadline" ||
    game.orderStatus === "orders_required" ||
    game.orderStatus === "orders_submitted"
  );
};

const visibleInMyGames = (game: Game) => !game.userInCivilDisorder;

const matchesView = (game: Game, view: ViewKey) => {
  if (!visibleInMyGames(game)) return false;
  if (view === "current") {
    return game.status === "pending" || game.status === "mustering" || game.status === "active";
  }
  if (view === "needs-you") return needsAttention(game);
  if (view === "finished") {
    return game.status === "completed" || game.status === "abandoned";
  }
  if (view === "sandbox") return game.sandbox === true;
  if (view === "active") return game.status === "active" && !game.sandbox;
  return game.status === view;
};

const actionSort = (first: Game, second: Game) => {
  const firstBadState = first.attention === "missed_deadline" ? 0 : 1;
  const secondBadState = second.attention === "missed_deadline" ? 0 : 1;
  return firstBadState - secondBadState || byDeadline(first, second);
};

const currentSections: GameSection[] = [
  {
    key: "attention",
    title: "Needs attention",
    attention: true,
    matches: needsAttention,
    sort: actionSort,
  },
  {
    key: "mustering",
    title: "Mustering",
    matches: game => game.status === "mustering" && !needsAttention(game),
    sort: byDeadline,
  },
  {
    key: "active",
    title: "Active",
    matches: game =>
      game.status === "active" && !game.sandbox && !needsAttention(game),
    sort: byActiveState,
  },
  {
    key: "pending",
    title: "Pending",
    matches: game => game.status === "pending",
    sort: byPendingFill,
  },
  {
    key: "sandbox",
    title: "Sandbox",
    matches: game => game.sandbox === true,
    sort: byDeadline,
  },
];

const sectionsForView = (view: ViewKey): GameSection[] => {
  if (view === "current") return currentSections;
  if (view === "needs-you") {
    return [
      {
        key: "mustering-attention",
        title: "Mustering",
        attention: true,
        matches: game => game.status === "mustering" && needsAttention(game),
        sort: actionSort,
      },
      {
        key: "active-attention",
        title: "Active",
        attention: true,
        matches: game => game.status === "active" && needsAttention(game),
        sort: actionSort,
      },
    ];
  }
  if (view === "mustering") {
    return [
      {
        key: "mustering-attention",
        title: "Needs attention",
        attention: true,
        matches: needsAttention,
        sort: actionSort,
      },
      {
        key: "mustering-waiting",
        title: "Waiting for others",
        matches: game => !needsAttention(game),
        sort: byDeadline,
      },
    ];
  }
  if (view === "active") {
    return [
      {
        key: "active-attention",
        title: "Needs attention",
        attention: true,
        matches: needsAttention,
        sort: actionSort,
      },
      {
        key: "active-current",
        title: "Active",
        matches: game => !needsAttention(game),
        sort: byActiveState,
      },
    ];
  }
  if (view === "finished") {
    return [
      {
        key: "completed",
        title: "Completed",
        matches: game => game.status === "completed",
        sort: (first, second) => first.name.localeCompare(second.name),
      },
      {
        key: "abandoned",
        title: "Abandoned",
        matches: game => game.status === "abandoned",
        sort: (first, second) => first.name.localeCompare(second.name),
      },
    ];
  }
  return [
    {
      key: view,
      title: views.find(option => option.key === view)?.label ?? view,
      matches: () => true,
      sort: view === "pending" ? byPendingFill : byDeadline,
    },
  ];
};

const preferenceLabel = (game: Game) => {
  const preferences = game.preferredNations ?? [];
  if (preferences.length === 0) return "No preferences";
  if (preferences.length === 1) return preferences[0];
  return `${preferences[0]} + ${preferences.length - 1}`;
};

const identityLabel = (game: Game) => {
  if (game.sandbox) return "Sandbox";
  if (game.status === "pending" || game.status === "mustering") {
    return preferenceLabel(game);
  }
  return game.nation ?? "Observer";
};

const gameSubtitle = (game: Game) => {
  if (game.status === "pending") {
    return game.isGameMaster ? "You are the game master" : "Waiting for players";
  }
  if (game.status === "mustering") {
    return `${game.confirmedPlayers ?? 0}/${game.playerCount} seats confirmed`;
  }
  if (game.status === "completed" || game.status === "abandoned") {
    return `${game.phase.season} ${game.phase.year}, ${game.phase.type}`;
  }
  if (game.sandbox) return "Classical sandbox";
  return `${game.phase.season} ${game.phase.year}, ${game.phase.type}`;
};

const gameState = (game: Game) => {
  if (game.status === "mustering" && game.musteringStatus === "unconfirmed") {
    return { label: `Confirm seat · ${game.phase.deadline}`, icon: AlertCircle, attention: true };
  }
  if (game.status === "mustering") {
    const waitingFor = game.playerCount - (game.confirmedPlayers ?? 0);
    return {
      label: `Confirmed · waiting for ${waitingFor}`,
      icon: CheckCircle2,
      attention: false,
    };
  }
  if (game.attention === "missed_deadline") {
    return { label: "Missed last deadline", icon: ShieldAlert, attention: true };
  }
  if (game.orderStatus === "orders_required" && game.status === "active") {
    return {
      label: `${game.phase.type} · ${game.phase.deadline}`,
      icon: Clock3,
      attention: true,
    };
  }
  if (game.orderStatus === "orders_submitted") {
    return {
      label: `Confirm orders · ${game.phase.deadline}`,
      icon: AlertCircle,
      attention: true,
    };
  }
  if (game.isPaused) return { label: "Paused", icon: Pause, attention: false };
  if (game.userEliminated) return { label: "Eliminated", icon: Skull, attention: false };
  if (game.otherPlayerInCivilDisorder) {
    return { label: "Replacement pending", icon: UserRound, attention: false };
  }
  if (game.replaceableSeat) {
    return { label: "Seat available", icon: UserRound, attention: false };
  }
  if (game.status === "pending") {
    return {
      label: `${game.members.length}/${game.playerCount} players`,
      icon: Users,
      attention: false,
    };
  }
  if (game.result === "solo_win") {
    return { label: "Solo victory", icon: Trophy, attention: false };
  }
  if (game.result === "solo_loss") {
    return { label: `Won by ${game.winner}`, icon: Trophy, attention: false };
  }
  if (game.result === "draw") return { label: "Draw", icon: Handshake, attention: false };
  if (game.status === "abandoned") {
    return { label: "Abandoned", icon: CircleDashed, attention: false };
  }
  if (game.sandbox) return { label: "Sandbox", icon: Clock3, attention: false };
  return {
    label: `Confirmed · ${game.phase.deadline}`,
    icon: CheckCircle2,
    attention: false,
  };
};

const SectionedGameCard: React.FC<{ game: Game }> = ({ game }) => {
  const state = gameState(game);
  const StateIcon = state.icon;

  return (
    <Card className="group cursor-pointer overflow-hidden py-0 transition-colors hover:border-foreground/20">
      <div className="relative h-28 overflow-hidden bg-muted sm:h-36">
        <StaticMap className="scale-110 object-cover opacity-90" />
        <div className="absolute inset-x-0 bottom-0 flex items-end justify-between gap-2 bg-gradient-to-t from-black/60 via-black/15 to-transparent p-3 pt-10">
          <Badge variant="secondary" className="max-w-[45%] gap-1.5 truncate bg-background/95">
            <UserRound className="size-3.5 shrink-0" />
            <span className="truncate">{identityLabel(game)}</span>
          </Badge>
          <Badge
            variant="outline"
            className={cn(
              "max-w-[65%] gap-1.5 truncate bg-background/95",
              state.attention &&
                "border-amber-300 bg-amber-50/95 text-amber-950 dark:border-amber-700 dark:bg-amber-950/95 dark:text-amber-100"
            )}
          >
            <StateIcon className="size-3.5 shrink-0" />
            <span className="truncate">{state.label}</span>
          </Badge>
        </div>
      </div>
      <CardContent className="p-3">
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0">
            <h3 className="truncate font-semibold">{game.name}</h3>
            <p className="truncate text-sm text-muted-foreground">
              {game.variant} · {gameSubtitle(game)}
            </p>
          </div>
          {game.unreadCount > 0 && (
            <Badge variant="secondary" className="shrink-0 gap-1">
              <Mail className="size-3" />
              {game.unreadCount}
            </Badge>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

const gamesById = (ids: string[]) => {
  const wanted = new Set(ids);
  return myGamesAllStates.filter(game => wanted.has(game.id));
};

const mixedGames = gamesById([
  "my-muster-unconfirmed",
  "my-muster-confirmed",
  "my-orders-required",
  "my-orders-unconfirmed",
  "my-orders-confirmed",
  "my-unread",
  "my-paused",
  "my-pending-owner",
  "my-finished-win",
  "my-finished-draw",
  "my-finished-abandoned",
  "my-civil-disorder",
  "my-sandbox",
]);

const orderingGames = gamesById([
  "my-muster-unconfirmed",
  "my-missed-deadline",
  "my-retreat",
  "my-adjustment",
  "my-orders-required",
  "my-orders-unconfirmed",
  "my-orders-confirmed",
  "my-civil-disorder",
]);

const quietGames = gamesById([
  "my-muster-confirmed",
  "my-orders-confirmed",
  "my-unread",
  "my-paused",
  "my-pending-joined",
  "my-sandbox",
]);

const historyGames = gamesById([
  "my-finished-win",
  "my-finished-loss",
  "my-finished-draw",
  "my-finished-abandoned",
]);

const gamesForState = (state: string): Game[] => {
  if (state === "empty") return [];
  if (state === "many") return myGamesMany;
  if (state === "ordering") return orderingGames;
  if (state === "quiet" || state === "filtered-empty") return quietGames;
  if (state === "history" || state === "current-empty") return historyGames;
  if (state === "mustering") {
    return gamesById(["my-muster-unconfirmed", "my-muster-confirmed"]);
  }
  if (state === "civil-disorder-hidden") {
    return gamesById([
      "my-civil-disorder",
      "my-orders-confirmed",
      "my-pending-joined",
    ]);
  }
  return mixedGames;
};

const initialView = (state: string): ViewKey => {
  if (state === "history") return "finished";
  if (state === "mustering") return "mustering";
  if (state === "filtered-empty") return "needs-you";
  return "current";
};

const SectionedSingleColumn: React.FC<{ state: string }> = ({ state }) => {
  const games = gamesForState(state);
  const [view, setView] = useState<ViewKey>(() => initialView(state));
  const visibleGames = games.filter(game => matchesView(game, view));
  const sections = sectionsForView(view)
    .map(section => ({
      ...section,
      games: visibleGames.filter(section.matches).sort(section.sort),
    }))
    .filter(section => section.games.length > 0);
  const activeView = views.find(option => option.key === view) ?? views[0];
  const countForView = (key: ViewKey) => games.filter(game => matchesView(game, key)).length;

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
          <div className="space-y-5">
            <div className="flex items-center justify-between gap-2 sm:hidden">
              <div className="flex h-9 items-center gap-2 rounded-full border bg-secondary px-3 text-sm font-medium">
                {activeView.label}
                <span className="text-muted-foreground">{visibleGames.length}</span>
              </div>
              <Sheet>
                <SheetTrigger asChild>
                  <Button variant="outline" size="sm">
                    <Filter />
                    Filters
                  </Button>
                </SheetTrigger>
                <SheetContent side="bottom" className="max-h-[85dvh] rounded-t-2xl">
                  <SheetHeader>
                    <SheetTitle>Show games</SheetTitle>
                    <SheetDescription>
                      Choose one view. Current keeps finished games out of the way.
                    </SheetDescription>
                  </SheetHeader>
                  <div className="overflow-y-auto px-4 pb-4">
                    <div className="overflow-hidden rounded-xl border">
                      {views.map(option => (
                        <SheetClose asChild key={option.key}>
                          <button
                            type="button"
                            aria-pressed={view === option.key}
                            onClick={() => setView(option.key)}
                            className="flex min-h-12 w-full items-center gap-3 border-b px-3 text-left text-sm last:border-b-0 hover:bg-muted"
                          >
                            <span className="flex-1 font-medium">{option.label}</span>
                            <span className="text-muted-foreground">
                              {countForView(option.key)}
                            </span>
                            <span className="flex size-5 items-center justify-center">
                              {view === option.key && <Check className="size-4" />}
                            </span>
                          </button>
                        </SheetClose>
                      ))}
                    </div>
                  </div>
                </SheetContent>
              </Sheet>
            </div>

            <div className="hidden flex-wrap gap-2 sm:flex" aria-label="View games">
              {views.map(option => (
                <Button
                  key={option.key}
                  size="sm"
                  variant={view === option.key ? "default" : "outline"}
                  aria-pressed={view === option.key}
                  onClick={() => setView(option.key)}
                  className="rounded-full"
                >
                  {option.label}
                  <span aria-hidden="true" className="opacity-70">
                    {countForView(option.key)}
                  </span>
                </Button>
              ))}
            </div>

            <p role="status" aria-live="polite" className="sr-only">
              {activeView.label}: {visibleGames.length} games
            </p>

            {sections.length === 0 ? (
              <Empty>
                <EmptyHeader>
                  <EmptyMedia variant="icon">
                    <SearchX />
                  </EmptyMedia>
                  <EmptyTitle>
                    {view === "current"
                      ? "No current games"
                      : `No games in ${activeView.label.toLowerCase()}`}
                  </EmptyTitle>
                  <EmptyDescription>
                    {view === "current"
                      ? "Find a game to join or create a new one."
                      : "Your games are still here. Choose another view to see them."}
                  </EmptyDescription>
                </EmptyHeader>
                <EmptyContent>
                  {view === "current" ? (
                    <div className="flex gap-2">
                      <Button>Find games</Button>
                      <Button variant="outline">Create a game</Button>
                    </div>
                  ) : (
                    <Button variant="outline" onClick={() => setView("current")}>
                      Show current games
                    </Button>
                  )}
                </EmptyContent>
              </Empty>
            ) : (
              <div className="space-y-7">
                {sections.map(section => (
                  <section key={section.key} className="space-y-3">
                    <div className="flex items-center gap-2">
                      {section.attention && (
                        <span className="size-2 rounded-full bg-amber-500" aria-hidden="true" />
                      )}
                      <h2 className="font-semibold">{section.title}</h2>
                      <Badge variant="secondary">{section.games.length}</Badge>
                    </div>
                    <div className="grid gap-3">
                      {section.games.map(game => (
                        <SectionedGameCard key={game.id} game={game} />
                      ))}
                    </div>
                  </section>
                ))}
              </div>
            )}
          </div>
        )}
      </ScreenContainer>
    </HomeShell>
  );
};

export { SectionedSingleColumn };
