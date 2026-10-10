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
  SheetTrigger,
} from "@/components/ui/sheet";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { HomeShell } from "@/components/HomeShell";
import { ScreenHeader } from "@/components/ScreenHeader";
import { StaticMap } from "@/components/StaticMap";
import { NationFlag } from "@/components/NationFlag";
import {
  myGamesCurrentActiveOrdering,
  myGamesCurrentAllCaughtUp,
  myGamesCurrentAttentionOrdering,
  myGamesCurrentDefault,
  myGamesCurrentEmpty,
  myGamesCurrentManaging,
  myGamesCurrentMany,
  myGamesCurrentRecentlyFinished,
  myGamesFinished,
  myGamesFinishedEmpty,
} from "@/data/fixtures";
import { cn } from "@/lib/utils";
import {
  AlertCircle,
  Check,
  CheckCircle2,
  CircleCheck,
  CircleDashed,
  Clock3,
  Handshake,
  History,
  Inbox,
  ListFilter,
  type LucideIcon,
  Mail,
  Pause,
  Skull,
  Trophy,
  UserRound,
  UserX,
  Users,
} from "lucide-react";
import { useState } from "react";
import type {
  MyGameEntry,
  MyGameState,
  MyGamesCurrentResponse,
  MyGamesFinishedResponse,
  MyGamesSectionKey,
} from "@/data/types";

type ViewKey = "current" | "finished";

const views: { key: ViewKey; label: string }[] = [
  { key: "current", label: "Current" },
  { key: "finished", label: "Finished" },
];

const sectionTitles: Record<MyGamesSectionKey, string> = {
  needs_attention: "Needs attention",
  managing: "Managing",
  mustering: "Mustering",
  active: "Active",
  pending: "Pending",
  recently_finished: "Recently finished",
  sandbox: "Sandbox",
};

interface StateBadge {
  label: string;
  icon: LucideIcon;
  attention: boolean;
}

const finishedLabel = (state: Extract<MyGameState, { kind: "finished" }>) => {
  const result = {
    solo_victory: "Solo victory",
    won_by: `Won by ${state.winner}`,
    draw: "Draw",
    abandoned: "Abandoned",
    ongoing: "game ongoing",
  }[state.result];
  if (!state.departure) return result;
  const departure = state.departure === "eliminated" ? "Eliminated" : "Civil disorder";
  return `${departure} · ${result}`;
};

const finishedIcon = (state: Extract<MyGameState, { kind: "finished" }>) => {
  if (state.departure === "eliminated") return Skull;
  if (state.departure === "civil_disorder") return UserX;
  if (state.result === "draw") return Handshake;
  if (state.result === "abandoned") return CircleDashed;
  return Trophy;
};

const stateBadge = (state: MyGameState): StateBadge | undefined => {
  switch (state.kind) {
    case "confirm_seat":
      return { label: `Confirm seat · ${state.timeRemaining} left`, icon: AlertCircle, attention: true };
    case "submit_orders":
      return { label: `Submit orders · ${state.timeRemaining} left`, icon: Clock3, attention: true };
    case "vote_on_draw":
      return { label: `Vote on draw · ${state.timeRemaining} left`, icon: Handshake, attention: true };
    case "seat_confirmed":
      return { label: `Seat confirmed · ${state.timeRemaining} left`, icon: CheckCircle2, attention: false };
    case "orders_unconfirmed":
      return { label: "Orders in · confirm to resolve early", icon: CircleDashed, attention: false };
    case "orders_confirmed":
      return { label: `Confirmed · Resolves in ${state.timeRemaining}`, icon: CheckCircle2, attention: false };
    case "mustering":
      return { label: `Mustering · ${state.timeRemaining} left`, icon: Users, attention: false };
    case "resolving":
      return { label: `Resolves in ${state.timeRemaining}`, icon: Clock3, attention: false };
    case "paused":
      return { label: "Paused", icon: Pause, attention: false };
    case "waiting_for_players":
      return { label: `${state.joined}/${state.total} players`, icon: Users, attention: false };
    case "sandbox":
      return undefined;
    case "finished":
      return { label: finishedLabel(state), icon: finishedIcon(state), attention: false };
  }
};

const subtitle = (game: MyGameEntry) => {
  if (game.status === "pending") return "Waiting for players";
  if (game.status === "mustering" && game.seatsConfirmed) {
    return `${game.seatsConfirmed.confirmed}/${game.seatsConfirmed.total} seats confirmed`;
  }
  if (!game.phase) return undefined;
  return `${game.phase.season} ${game.phase.year}, ${game.phase.type}`;
};

const IdentityBadge: React.FC<{ game: MyGameEntry }> = ({ game }) => {
  if (game.state.kind === "sandbox") {
    return (
      <Badge
        variant="secondary"
        className="absolute bottom-2 left-2 max-w-[40%] gap-1.5 truncate bg-background/95 md:right-2 md:left-auto md:max-w-[calc(100%-1rem)]"
      >
        <UserRound className="size-3.5 shrink-0" />
        <span className="truncate">Sandbox</span>
      </Badge>
    );
  }
  if (!game.nation) return null;
  return (
    <Badge
      variant="secondary"
      className="absolute bottom-2 left-2 max-w-[40%] gap-1.5 truncate bg-background/95 md:right-2 md:left-auto md:max-w-[calc(100%-1rem)]"
    >
      <NationFlag nation={game.nation} size="sm" />
      <span className="truncate">{game.nation}</span>
    </Badge>
  );
};

const attentionClasses =
  "border-amber-300 bg-amber-50 text-amber-950 dark:border-amber-700 dark:bg-amber-950 dark:text-amber-100";

const GameCard: React.FC<{ game: MyGameEntry }> = ({ game }) => {
  const badge = stateBadge(game.state);
  const BadgeIcon = badge?.icon;
  const gameSubtitle = subtitle(game);
  const hasIdentity = game.state.kind === "sandbox" || game.nation !== undefined;

  return (
    <Card
      className={cn(
        "group flex w-full cursor-pointer flex-col overflow-hidden py-0 transition-colors hover:border-foreground/20 md:flex-row",
        game.state.kind === "paused" && "opacity-60"
      )}
    >
      <div className="relative h-40 w-full shrink-0 overflow-hidden bg-muted md:h-44 md:w-48">
        <StaticMap className="scale-110 object-cover opacity-90" />
        <IdentityBadge game={game} />
        {badge && BadgeIcon && (
          <Badge
            variant="outline"
            className={cn(
              "absolute right-2 bottom-2 gap-1.5 truncate bg-background/95 md:hidden",
              hasIdentity ? "max-w-[58%]" : "max-w-[calc(100%-1rem)]",
              badge.attention && attentionClasses
            )}
          >
            <BadgeIcon className="size-3.5 shrink-0" />
            <span className="truncate">{badge.label}</span>
          </Badge>
        )}
      </div>
      <CardContent className="flex min-w-0 flex-grow flex-col gap-2 p-4 md:py-2">
        <div className="flex w-full items-start justify-between gap-2">
          <div className="min-w-0 flex-1">
            <h3 className="truncate font-semibold">{game.name}</h3>
            {gameSubtitle && (
              <p className="truncate text-sm text-muted-foreground">{gameSubtitle}</p>
            )}
            {badge && BadgeIcon && (
              <Badge
                variant="outline"
                className={cn(
                  "mt-3 hidden max-w-full gap-1.5 truncate bg-background md:inline-flex",
                  badge.attention && attentionClasses
                )}
              >
                <BadgeIcon className="size-3.5 shrink-0" />
                <span className="truncate">{badge.label}</span>
              </Badge>
            )}
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

const AllCaughtUp: React.FC = () => (
  <div className="flex items-center gap-2 text-sm text-muted-foreground">
    <CircleCheck className="size-4" aria-hidden="true" />
    <span>You're all caught up</span>
  </div>
);

const CurrentView: React.FC<{
  response: MyGamesCurrentResponse;
  onShowFinished: () => void;
}> = ({ response, onShowFinished }) => {
  if (response.sections.length === 0) {
    return (
      <Empty>
        <EmptyHeader>
          <EmptyMedia variant="icon">
            <Inbox />
          </EmptyMedia>
          <EmptyTitle>No current games</EmptyTitle>
          <EmptyDescription>Find a game to join or create a new one.</EmptyDescription>
        </EmptyHeader>
        <EmptyContent>
          <div className="flex flex-wrap justify-center gap-2">
            <Button>Find games</Button>
            <Button variant="outline">Create a game</Button>
          </div>
          <Button variant="link" onClick={onShowFinished}>
            Show finished games
          </Button>
        </EmptyContent>
      </Empty>
    );
  }

  const hasAttention = response.sections.some(section => section.key === "needs_attention");

  return (
    <div className="space-y-7">
      {!hasAttention && <AllCaughtUp />}
      {response.sections.map(section => (
        <section key={section.key} className="space-y-3">
          <div className="flex items-center gap-2">
            {section.key === "needs_attention" && (
              <span className="size-2 rounded-full bg-amber-500" aria-hidden="true" />
            )}
            <h2 className="font-semibold">{sectionTitles[section.key]}</h2>
          </div>
          <div className="grid gap-3">
            {section.games.map(game => (
              <GameCard key={game.id} game={game} />
            ))}
          </div>
        </section>
      ))}
    </div>
  );
};

const FinishedView: React.FC<{ response: MyGamesFinishedResponse }> = ({ response }) => {
  if (response.results.length === 0) {
    return (
      <Empty>
        <EmptyHeader>
          <EmptyMedia variant="icon">
            <History />
          </EmptyMedia>
          <EmptyTitle>No finished games yet</EmptyTitle>
          <EmptyDescription>
            Games you finish, leave or are eliminated from will appear here.
          </EmptyDescription>
        </EmptyHeader>
      </Empty>
    );
  }

  return (
    <div className="grid gap-3">
      {response.results.map(game => (
        <GameCard key={game.id} game={game} />
      ))}
    </div>
  );
};

const currentForState = (state: string): MyGamesCurrentResponse => {
  if (state === "needs-attention") return myGamesCurrentAttentionOrdering;
  if (state === "active-ordering") return myGamesCurrentActiveOrdering;
  if (state === "all-caught-up") return myGamesCurrentAllCaughtUp;
  if (state === "managing") return myGamesCurrentManaging;
  if (state === "recently-finished") return myGamesCurrentRecentlyFinished;
  if (state === "current-empty" || state === "no-games") return myGamesCurrentEmpty;
  if (state === "many") return myGamesCurrentMany;
  return myGamesCurrentDefault;
};

const finishedForState = (state: string): MyGamesFinishedResponse =>
  state === "no-games" ? myGamesFinishedEmpty : myGamesFinished;

const ViewOptions: React.FC<{
  view: ViewKey;
  onSelect: (view: ViewKey) => void;
  closeOnSelect: boolean;
}> = ({ view, onSelect, closeOnSelect }) => (
  <div className="grid gap-1" aria-label="View games">
    {views.map(option => {
      const button = (
        <Button
          key={option.key}
          type="button"
          variant={view === option.key ? "secondary" : "ghost"}
          aria-pressed={view === option.key}
          onClick={() => onSelect(option.key)}
          className="h-11 justify-between px-3 sm:h-9"
        >
          <span>{option.label}</span>
          {view === option.key && <Check className="size-4" />}
        </Button>
      );
      return closeOnSelect ? (
        <SheetClose asChild key={option.key}>
          {button}
        </SheetClose>
      ) : (
        button
      );
    })}
  </div>
);

const ServerSections: React.FC<{ state: string }> = ({ state }) => {
  const current = currentForState(state);
  const finished = finishedForState(state);
  const hasGames = current.sections.length > 0 || finished.results.length > 0;
  const [view, setView] = useState<ViewKey>(() =>
    state === "finished" ? "finished" : "current"
  );
  const [desktopOpen, setDesktopOpen] = useState(false);
  const activeView = views.find(option => option.key === view) ?? views[0];

  return (
    <HomeShell activeNavItem="My Games">
      <ScreenContainer>
        <ScreenHeader
          title="My Games"
          actions={
            hasGames ? (
              <div className="flex items-center">
                <Sheet>
                  <SheetTrigger asChild>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="relative sm:hidden"
                      aria-label={`Choose game view, ${activeView.label} selected`}
                    >
                      <ListFilter />
                      {view !== "current" && (
                        <span
                          className="absolute top-1.5 right-1.5 size-2 rounded-full bg-primary ring-2 ring-background"
                          aria-hidden="true"
                        />
                      )}
                    </Button>
                  </SheetTrigger>
                  <SheetContent side="bottom" className="max-h-[85dvh] gap-0 rounded-t-2xl">
                    <div className="overflow-y-auto p-2">
                      <ViewOptions view={view} onSelect={setView} closeOnSelect />
                    </div>
                  </SheetContent>
                </Sheet>
                <Popover open={desktopOpen} onOpenChange={setDesktopOpen}>
                  <PopoverTrigger asChild>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="hidden sm:inline-flex"
                      aria-label={`Choose game view, ${activeView.label} selected`}
                    >
                      <span>{activeView.label}</span>
                      <ListFilter />
                    </Button>
                  </PopoverTrigger>
                  <PopoverContent align="end" className="w-64 p-2">
                    <ViewOptions
                      view={view}
                      onSelect={next => {
                        setView(next);
                        setDesktopOpen(false);
                      }}
                      closeOnSelect={false}
                    />
                  </PopoverContent>
                </Popover>
              </div>
            ) : undefined
          }
        />
        {!hasGames ? (
          <Empty>
            <EmptyHeader>
              <EmptyMedia variant="icon">
                <Inbox />
              </EmptyMedia>
              <EmptyTitle>No games yet</EmptyTitle>
              <EmptyDescription>Games you create or join will appear here.</EmptyDescription>
            </EmptyHeader>
            <EmptyContent>
              <div className="flex gap-2">
                <Button>Create a game</Button>
                <Button variant="outline">Find a game</Button>
              </div>
            </EmptyContent>
          </Empty>
        ) : view === "current" ? (
          <CurrentView response={current} onShowFinished={() => setView("finished")} />
        ) : (
          <FinishedView response={finished} />
        )}
      </ScreenContainer>
    </HomeShell>
  );
};

export { ServerSections };
