import React from "react";
import { Link } from "react-router";
import {
  AlertCircle,
  CheckCircle2,
  CircleDashed,
  Clock3,
  Handshake,
  LogOut,
  Mail,
  Pause,
  Skull,
  Trophy,
  UserRound,
  UserX,
  Users,
  type LucideIcon,
} from "lucide-react";
import type { MyGame, MyGameState } from "@/api/generated/endpoints";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { MapView } from "@/components/MapView";
import {
  NationFlag,
  findNationColor,
  findNationFlagUrl,
} from "@/components/NationFlag";
import { useGameVariant } from "@/hooks/useGameVariant";
import { useIsMobile } from "@/hooks/use-mobile";
import { cn } from "@/lib/utils";
import { formatTimeLeft, getGameLandingPath } from "@/util";

interface MyGameCardProps {
  game: MyGame;
}

const resultLabels = {
  solo_victory: "Solo victory",
  draw: "Draw",
  abandoned: "Abandoned",
  ongoing: "game ongoing",
};

const departureBadges = {
  eliminated: { label: "Eliminated", icon: Skull },
  civil_disorder: { label: "Civil disorder", icon: UserX },
  withdrawn: { label: "Withdrew", icon: LogOut },
  removed: { label: "Removed", icon: UserX },
};

const resultIcons = {
  solo_victory: Trophy,
  won_by: Trophy,
  draw: Handshake,
  abandoned: CircleDashed,
  ongoing: CircleDashed,
};

const finishedBadge = (state: MyGameState) => {
  if (!state.result) return null;
  const result =
    state.result === "won_by"
      ? `Won by ${state.winner}`
      : resultLabels[state.result];
  if (!state.departure) {
    return { label: result, icon: resultIcons[state.result] };
  }
  const departure = departureBadges[state.departure];
  return { label: `${departure.label} · ${result}`, icon: departure.icon };
};

const timed = (label: string, deadline: string | null, suffix = " left") =>
  deadline ? `${label} · ${formatTimeLeft(deadline)}${suffix}` : label;

const stateBadge = (
  game: MyGame
): { label: string; icon: LucideIcon } | null => {
  const { state } = game;
  switch (state.kind) {
    case "confirm_seat":
      return { label: timed("Confirm seat", state.deadline), icon: AlertCircle };
    case "submit_orders":
      return { label: timed("Submit orders", state.deadline), icon: Clock3 };
    case "vote_on_draw":
      return { label: timed("Vote on draw", state.deadline), icon: Handshake };
    case "seat_confirmed":
      return { label: timed("Seat confirmed", state.deadline), icon: CheckCircle2 };
    case "orders_unconfirmed":
      return { label: "Orders in · confirm to resolve early", icon: CircleDashed };
    case "orders_confirmed":
      return {
        label: state.deadline
          ? `Confirmed · Resolves in ${formatTimeLeft(state.deadline)}`
          : "Confirmed",
        icon: CheckCircle2,
      };
    case "resolving":
      return state.deadline
        ? { label: `Resolves in ${formatTimeLeft(state.deadline)}`, icon: Clock3 }
        : null;
    case "mustering":
      return { label: timed("Mustering", state.deadline), icon: Users };
    case "waiting_for_players":
      return game.seats
        ? { label: `${game.seats.filled}/${game.seats.total} players`, icon: Users }
        : null;
    case "paused":
      return { label: "Paused", icon: Pause };
    case "sandbox":
      return null;
    case "finished":
      return finishedBadge(state);
  }
};

const attentionKinds: ReadonlyArray<MyGameState["kind"]> = [
  "confirm_seat",
  "submit_orders",
  "vote_on_draw",
];

const subtitle = (game: MyGame) => {
  if (game.status === "pending") return "Waiting for players";
  if (game.status === "mustering" && game.seats) {
    return `${game.seats.filled}/${game.seats.total} seats confirmed`;
  }
  if (!game.currentPhase) return null;
  const { season, year, type } = game.currentPhase;
  return `${season} ${year}, ${type}`;
};

const MyGameCard: React.FC<MyGameCardProps> = ({ game }) => {
  const variant = useGameVariant(game);
  const isMobile = useIsMobile();
  const badge = stateBadge(game);
  const gameSubtitle = subtitle(game);

  const stateBadgeElement = badge && (
    <Badge
      variant="outline"
      className={cn(
        "max-w-full bg-background",
        isMobile && "absolute bottom-2 right-2 max-w-[58%]",
        attentionKinds.includes(game.state.kind) &&
          "border-orange-400 bg-amber-50 text-amber-950 dark:bg-amber-100 dark:text-amber-950",
        game.state.kind === "orders_confirmed" && "border-green-600 dark:border-green-500"
      )}
    >
      <badge.icon />
      <span className="truncate">{badge.label}</span>
    </Badge>
  );

  const identityClassName =
    "absolute bottom-2 left-2 max-w-[40%] bg-background/95 md:left-auto md:right-2 md:max-w-[calc(100%-1rem)]";

  const identityBadge = game.sandbox ? (
    <Badge variant="secondary" className={identityClassName}>
      <UserRound />
      Sandbox
    </Badge>
  ) : (
    game.nation &&
    variant && (
      <Badge variant="secondary" className={identityClassName}>
        <NationFlag
          flagUrl={findNationFlagUrl(variant.nations, game.nation)}
          color={findNationColor(variant.nations, game.nation)}
          alt={game.nation}
          size="sm"
        />
        <span className="truncate">{game.nation}</span>
      </Badge>
    )
  );

  return (
    <Link to={getGameLandingPath(game, isMobile)} className="block">
      <Card
        className={cn(
          "overflow-hidden p-0 transition-colors hover:border-foreground/20 md:flex-row",
          game.state.kind === "paused" && "opacity-60"
        )}
      >
        <div className="relative h-40 shrink-0 overflow-hidden md:h-44 md:w-48">
          {variant ? (
            <MapView
              mode="static"
              variant={variant}
              phase={game.currentPhase ?? variant.templatePhase}
              cover
              className="w-full h-full"
            />
          ) : (
            <Skeleton className="h-full w-full rounded-none" />
          )}
          {identityBadge}
          {isMobile && stateBadgeElement}
        </div>
        <div className="flex min-w-0 flex-grow items-start justify-between gap-2 p-4 md:py-3">
          <div className="flex min-w-0 flex-col gap-1">
            <h3 className="truncate font-semibold">{game.name}</h3>
            {gameSubtitle && (
              <p className="truncate text-sm text-muted-foreground">{gameSubtitle}</p>
            )}
            {!isMobile && stateBadgeElement && (
              <div className="mt-2">{stateBadgeElement}</div>
            )}
          </div>
          {game.unreadCount > 0 && (
            <Badge>
              <Mail />
              {game.unreadCount}
            </Badge>
          )}
        </div>
      </Card>
    </Link>
  );
};

export { MyGameCard };
