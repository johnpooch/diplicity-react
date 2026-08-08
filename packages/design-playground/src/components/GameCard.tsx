import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { NationAvatar } from "@/components/NationAvatar";
import { StaticMap } from "@/components/StaticMap";
import { cn } from "@/lib/utils";
import { Clock, Lock, MessageSquare, Users } from "lucide-react";
import type { Game, OrderStatus } from "@/data/types";

const orderStatusLabel: Record<OrderStatus, string> = {
  orders_required: "Orders required",
  orders_submitted: "Orders submitted",
  orders_confirmed: "Confirmed",
  no_orders_required: "No orders required",
};

const orderStatusVariant: Record<
  OrderStatus,
  "default" | "secondary" | "outline"
> = {
  orders_required: "default",
  orders_submitted: "secondary",
  orders_confirmed: "secondary",
  no_orders_required: "outline",
};

interface GameCardProps {
  game: Game;
  className?: string;
}

const GameCard: React.FC<GameCardProps> = ({ game, className }) => {
  const { phase } = game;

  return (
    <Card className={cn("overflow-hidden py-0", className)}>
      <CardContent className="flex gap-3 p-3">
        <div className="size-16 shrink-0 overflow-hidden rounded-md border bg-muted sm:size-24">
          <StaticMap />
        </div>

        <div className="flex min-w-0 flex-1 flex-col gap-2">
          <div className="flex items-start justify-between gap-2">
            <div className="min-w-0">
              <div className="flex items-center gap-1.5">
                <h3 className="truncate font-semibold leading-tight">
                  {game.name}
                </h3>
                {game.isPrivate && (
                  <Lock className="size-3.5 shrink-0 text-muted-foreground" />
                )}
              </div>
              <p className="truncate text-sm text-muted-foreground">
                {game.variant}
                {game.status === "completed"
                  ? ` · Won by ${game.winner}`
                  : ` · ${phase.season} ${phase.year} ${phase.type}`}
              </p>
            </div>
            {game.unreadCount > 0 && (
              <Badge className="shrink-0 gap-1" variant="secondary">
                <MessageSquare className="size-3" />
                {game.unreadCount}
              </Badge>
            )}
          </div>

          <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-sm text-muted-foreground">
            {game.status === "pending" ? (
              <span className="flex items-center gap-1">
                <Users className="size-3.5" />
                {game.members.length} of {game.playerCount} joined
              </span>
            ) : (
              <span className="flex items-center gap-1">
                <Clock className="size-3.5" />
                {phase.deadline}
              </span>
            )}
          </div>

          <div className="flex flex-wrap items-center justify-between gap-2">
            <div className="flex -space-x-1">
              {game.members.map(member => (
                <NationAvatar
                  key={member.nation}
                  nation={member.nation}
                  className="size-7 ring-2 ring-card"
                />
              ))}
            </div>
            {game.status === "active" ? (
              <Badge variant={orderStatusVariant[game.orderStatus]}>
                {orderStatusLabel[game.orderStatus]}
              </Badge>
            ) : game.status === "pending" ? (
              <Button size="sm" variant="outline">
                Join
              </Button>
            ) : null}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export { GameCard };
