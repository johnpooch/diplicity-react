import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { StaticMap } from "@/components/StaticMap";
import { cn } from "@/lib/utils";
import {
  AlertTriangle,
  CheckCircle2,
  CircleDashed,
  Clock3,
  Crown,
  Handshake,
  Mail,
  Pause,
  ShieldAlert,
  Skull,
  Trophy,
  UserRound,
  Users,
} from "lucide-react";
import type { Game, GameAttention } from "@/data/types";

const attentionPriority: Record<GameAttention, number> = {
  confirm_seat: 0,
  last_seat_to_confirm: 1,
  civil_disorder: 2,
  missed_deadline: 3,
  orders_required: 4,
  orders_unconfirmed: 5,
  unread_messages: 6,
  none: 7,
};

const gameNeedsAction = (game: Game) =>
  game.attention !== undefined && game.attention !== "none";

const sortByAttention = (games: Game[]) =>
  [...games].sort((first, second) => {
    const firstRank = first.urgencyRank ?? 1000;
    const secondRank = second.urgencyRank ?? 1000;
    if (firstRank !== secondRank) return firstRank - secondRank;
    const firstPriority = attentionPriority[first.attention ?? "none"];
    const secondPriority = attentionPriority[second.attention ?? "none"];
    if (firstPriority !== secondPriority) return firstPriority - secondPriority;
    if (first.sandbox !== second.sandbox) return first.sandbox ? 1 : -1;
    return first.name.localeCompare(second.name);
  });

const preferenceLabel = (game: Game) => {
  const preferences = game.preferredNations ?? [];
  if (preferences.length === 0) return "Select nation";
  if (preferences.length === 1) return preferences[0];
  return `${preferences[0]} + ${preferences.length - 1}`;
};

const identityLabel = (game: Game) => {
  if (game.sandbox) return "Practice";
  if (game.status === "pending" || game.status === "mustering") {
    return preferenceLabel(game);
  }
  return game.nation ?? "Observer";
};

const resultLabel = (game: Game) => {
  if (game.result === "solo_win") return "Solo victory";
  if (game.result === "solo_loss") return `Won by ${game.winner}`;
  if (game.result === "draw") return "Draw";
  return "Abandoned";
};

const actionLabel = (game: Game) => {
  if (game.attention === "confirm_seat") return "Confirm your seat";
  if (game.attention === "last_seat_to_confirm") return "You are last to confirm";
  if (game.attention === "civil_disorder") return "Recover your position";
  if (game.attention === "missed_deadline") return "You missed the last deadline";
  if (game.attention === "orders_required") return `${game.phase.type} orders due`;
  if (game.attention === "orders_unconfirmed") return "Orders not confirmed";
  if (game.attention === "unread_messages") return `${game.unreadCount} unread messages`;
  if (game.isPaused) return "Paused";
  if (game.userEliminated) return "Eliminated";
  if (game.otherPlayerInCivilDisorder) return "Player in civil disorder";
  if (game.replaceableSeat) return "Seat available";
  if (game.status === "pending") {
    return `${game.members.length}/${game.playerCount} players`;
  }
  if (game.status === "mustering") {
    return game.musteringStatus === "confirmed" ? "Seat confirmed" : "Mustering";
  }
  if (game.status === "completed" || game.status === "abandoned") {
    return resultLabel(game);
  }
  if (game.sandbox) return "Resume practice";
  if (game.orderStatus === "orders_confirmed") return "Orders confirmed";
  return game.phase.deadline;
};

const actionIcon = (game: Game) => {
  if (game.result === "solo_win" || game.result === "solo_loss") return Trophy;
  if (game.result === "draw") return Handshake;
  if (game.status === "abandoned") return CircleDashed;
  if (game.userEliminated) return Skull;
  if (game.isPaused) return Pause;
  if (game.userInCivilDisorder || game.attention === "missed_deadline") {
    return ShieldAlert;
  }
  if (game.attention === "unread_messages") return Mail;
  if (game.musteringStatus === "confirmed" || game.orderStatus === "orders_confirmed") {
    return CheckCircle2;
  }
  if (game.status === "pending") return Users;
  if (game.status === "mustering") return AlertTriangle;
  return Clock3;
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
  if (game.sandbox) return "Classical practice board";
  return `${game.phase.season} ${game.phase.year}, ${game.phase.type}`;
};

interface MyGameCardProps {
  game: Game;
  prominent?: boolean;
}

const MyGameCard: React.FC<MyGameCardProps> = ({ game, prominent = false }) => {
  const ActionIcon = actionIcon(game);
  const urgent = game.attention === "confirm_seat" || game.attention === "last_seat_to_confirm";

  return (
    <Card
      className={cn(
        "overflow-hidden py-0",
        urgent && "border-destructive/60 shadow-sm shadow-destructive/10"
      )}
    >
      <div
        className={cn(
          "relative h-28 overflow-hidden bg-muted sm:h-36",
          prominent && "h-36 sm:h-48"
        )}
      >
        <StaticMap className="scale-110 object-cover opacity-90" />
        <div className="absolute inset-x-0 bottom-0 flex items-end justify-between gap-2 bg-gradient-to-t from-black/65 via-black/20 to-transparent p-3 pt-10">
          <Badge variant="secondary" className="max-w-[55%] gap-1.5 truncate bg-background/95">
            <UserRound className="size-3.5 shrink-0" />
            <span className="truncate">{identityLabel(game)}</span>
          </Badge>
          <Badge
            variant={urgent ? "destructive" : "secondary"}
            className={cn(
              "max-w-[55%] gap-1.5 truncate",
              !urgent && "bg-background/95 text-foreground"
            )}
          >
            <ActionIcon className="size-3.5 shrink-0" />
            <span className="truncate">{actionLabel(game)}</span>
          </Badge>
        </div>
      </div>
      <CardContent className="space-y-3 p-3">
        <div className="min-w-0">
          <div className="flex items-start justify-between gap-2">
            <h3 className="truncate font-semibold">{game.name}</h3>
            {game.unreadCount > 0 && game.attention !== "unread_messages" && (
              <Badge variant="secondary" className="shrink-0 gap-1">
                <Mail className="size-3" />
                {game.unreadCount}
              </Badge>
            )}
          </div>
          <p className="text-sm text-muted-foreground">
            {game.variant} · {gameSubtitle(game)}
          </p>
        </div>
        {urgent && (
          <div className="flex items-center justify-between gap-3 rounded-md bg-destructive/10 p-2.5">
            <div className="min-w-0">
              <p className="text-sm font-medium">{game.phase.deadline}</p>
              <p className="truncate text-xs text-muted-foreground">
                Review the game before committing.
              </p>
            </div>
            <Button size="sm" className="shrink-0">
              Review
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

const CompactGameRow: React.FC<{ game: Game }> = ({ game }) => {
  const ActionIcon = actionIcon(game);
  const urgent = gameNeedsAction(game);

  return (
    <div className="flex items-center gap-3 px-3 py-3">
      <div className="size-12 shrink-0 overflow-hidden rounded-md border bg-muted">
        <StaticMap className="scale-125 object-cover" />
      </div>
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-1.5">
          <p className="truncate text-sm font-medium">{game.name}</p>
          {game.isGameMaster && <Crown className="size-3.5 shrink-0 text-muted-foreground" />}
        </div>
        <p className="truncate text-xs text-muted-foreground">
          {identityLabel(game)} · {gameSubtitle(game)}
        </p>
      </div>
      <div className={cn("flex max-w-36 items-center gap-1 text-right text-xs", urgent ? "font-medium text-foreground" : "text-muted-foreground")}>
        <ActionIcon className="size-3.5 shrink-0" />
        <span className="line-clamp-2">{actionLabel(game)}</span>
      </div>
    </div>
  );
};

const MusteringAlert: React.FC<{ games: Game[] }> = ({ games }) => {
  const atRisk = sortByAttention(games).find(
    game => game.attention === "confirm_seat" || game.attention === "last_seat_to_confirm"
  );
  if (!atRisk) return null;

  return (
    <div className="flex items-center gap-3 rounded-lg border border-destructive/50 bg-destructive/10 p-3">
      <AlertTriangle className="size-5 shrink-0 text-destructive" />
      <div className="min-w-0 flex-1">
        <p className="text-sm font-semibold">Your seat can be released</p>
        <p className="truncate text-xs text-muted-foreground">
          {atRisk.name} · {atRisk.phase.deadline}
        </p>
      </div>
      <Button size="sm" variant="outline" className="shrink-0 bg-background">
        Review
      </Button>
    </div>
  );
};

const ResultCount: React.FC<{ count: number }> = ({ count }) => (
  <p role="status" aria-live="polite" className="text-sm text-muted-foreground">
    {count} {count === 1 ? "game" : "games"}
  </p>
);

export {
  CompactGameRow,
  gameNeedsAction,
  MusteringAlert,
  MyGameCard,
  ResultCount,
  sortByAttention,
};
