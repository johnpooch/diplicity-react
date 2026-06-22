import React from "react";
import { useNavigate } from "react-router";
import { toast } from "sonner";
import { useQueryClient } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { Variant } from "../api/generated/endpoints";
import {
  Card,
  CardDescription,
  CardHeader,
  CardTitle,
  CardFooter,
} from "@/components/ui/card";
import { GameDropdownMenu } from "./GameDropdownMenu";
import { NationBadge } from "./NationBadge";
import {
  UserPlus,
  Lock,
  MessageSquareOff,
  Mail,
  Clock,
  Check,
  AlertTriangle,
  UserX,
  Pause,
  Trophy,
  Users,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { RemainingTimeDisplay } from "./RemainingTimeDisplay";
import {
  GameList,
  useGameJoinCreate,
  getGamesListQueryKey,
} from "../api/generated/endpoints";
import { formatTimeAgo, getGameLandingPath } from "../util";
import { Skeleton } from "./ui/skeleton";
import { Tooltip, TooltipContent, TooltipTrigger } from "./ui/tooltip";
import { useIsMobile } from "@/hooks/use-mobile";
import { useCheckNotificationPermission } from "@/hooks/useCheckNotificationPermission";

export interface GameCardProps {
  game: GameList;
  variant: Pick<Variant, "name" | "id" | "nations">;
  map: React.ReactNode;
  className?: string;
}

const ORDER_STATUS_CONFIG: Record<
  string,
  { label: string; badgeClassName: string; icon: React.ReactNode; tooltip: string }
> = {
  orders_required: {
    label: "Orders required",
    badgeClassName: "bg-amber-500 text-white hover:bg-amber-500",
    icon: <Clock className="size-3" />,
    tooltip: "You have orders to submit this phase",
  },
  orders_submitted: {
    label: "Orders submitted",
    badgeClassName: "bg-green-600 text-white hover:bg-green-600",
    icon: <Check className="size-3" />,
    tooltip: "Your orders are submitted for this phase",
  },
  orders_not_confirmed: {
    label: "Orders not confirmed",
    badgeClassName: "bg-amber-500 text-white hover:bg-amber-500",
    icon: <Clock className="size-3" />,
    tooltip: "You have entered orders but not confirmed them for this phase",
  },
  no_orders_required: {
    label: "Orders not required",
    badgeClassName: "bg-slate-900 text-white hover:bg-slate-900",
    icon: <Check className="size-3" />,
    tooltip: "No orders are needed from you this phase",
  },
};

const GameCard: React.FC<GameCardProps> = ({ game, variant, map }) => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const isMobile = useIsMobile();
  const phase = game.currentPhase;
  const playerNation = game.members.find(m => m.isCurrentUser)?.nation ?? null;
  const joinGameMutation = useGameJoinCreate();
  const checkNotificationPermission = useCheckNotificationPermission();

  const isActive = game.status === "active";
  const isPending = game.status === "pending";
  const isAbandoned = game.status === "abandoned";
  const isFinished = game.status === "completed" || isAbandoned;
  const showAvatars = !game.sandbox;
  const totalSlots = variant.nations.length;
  const joinedCount = game.members.length;
  const winnerIds = new Set(game.victory?.members.map(m => m.id) ?? []);

  const handleClickGame = () => {
    navigate(getGameLandingPath(game, isMobile));
  };

  const handleClickGameInfo = () => {
    navigate(`/game-info/${game.id}`);
  };

  const handleClickPlayerInfo = () => {
    navigate(`/player-info/${game.id}`);
  };

  const handleJoinGame = async () => {
    try {
      await joinGameMutation.mutateAsync({ gameId: game.id, data: {} });
      toast.success("Successfully joined game");
      queryClient.invalidateQueries({ queryKey: getGamesListQueryKey() });
      if (!game.sandbox) {
        checkNotificationPermission();
      }
    } catch {
      toast.error("Failed to join game");
    }
  };

  const joinGameButton = game.canJoin && (
    <Tooltip>
      <TooltipTrigger asChild>
        <Button onClick={handleJoinGame} variant="outline" aria-label="Join game">
          <UserPlus className="size-4" />
        </Button>
      </TooltipTrigger>
      <TooltipContent>
        <p>Join game</p>
      </TooltipContent>
    </Tooltip>
  );

  const orderStatusConfig = game.orderStatus
    ? ORDER_STATUS_CONFIG[game.orderStatus]
    : undefined;

  const gunboatBadge = game.pressType === "no_press" && (
    <Tooltip>
      <TooltipTrigger asChild>
        <Badge variant="secondary" className="gap-1" aria-label="Gunboat">
          <MessageSquareOff className="size-3" />
          Gunboat
        </Badge>
      </TooltipTrigger>
      <TooltipContent>No private messaging is allowed in this game</TooltipContent>
    </Tooltip>
  );

  const cdBadge = game.memberStatus?.includes("civil_disorder") && (
    <Tooltip>
      <TooltipTrigger asChild>
        <Badge variant="destructive" className="gap-1">
          <UserX className="size-3" />
          CD
        </Badge>
      </TooltipTrigger>
      <TooltipContent>
        Civil Disorder — your units are acting without orders
      </TooltipContent>
    </Tooltip>
  );

  const resultBadge = (() => {
    if (isAbandoned) {
      return (
        <Badge variant="secondary" className="gap-1">
          <UserX className="size-3" />
          Abandoned
        </Badge>
      );
    }
    if (!game.victory) return null;
    if (game.victory.type === "solo") {
      const winner = game.victory.members[0];
      const content = (
        <span className="inline-flex items-center gap-1">
          <Trophy className="size-3" />
          {winner?.nation ?? winner?.name ?? "Winner"} won
        </span>
      );
      return (
        <Tooltip>
          <TooltipTrigger asChild>
            {winner?.nation ? (
              <NationBadge nations={variant.nations} nation={winner.nation}>
                {content}
              </NationBadge>
            ) : (
              <Badge className="gap-1">{content}</Badge>
            )}
          </TooltipTrigger>
          <TooltipContent>Solo victory</TooltipContent>
        </Tooltip>
      );
    }
    return (
      <Tooltip>
        <TooltipTrigger asChild>
          <Badge variant="secondary" className="gap-1">
            <Users className="size-3" />
            Draw · {game.victory.members.length} players
          </Badge>
        </TooltipTrigger>
        <TooltipContent>The game ended in a draw</TooltipContent>
      </Tooltip>
    );
  })();

  const badgeCluster = (
    <div className="flex flex-wrap items-center gap-2">
      {isActive && orderStatusConfig && (
        <Tooltip>
          <TooltipTrigger asChild>
            <Badge className={`gap-1 ${orderStatusConfig.badgeClassName}`}>
              {orderStatusConfig.icon}
              {orderStatusConfig.label}
            </Badge>
          </TooltipTrigger>
          <TooltipContent>{orderStatusConfig.tooltip}</TooltipContent>
        </Tooltip>
      )}
      {isActive && game.memberStatus?.includes("nmr") && (
        <Tooltip>
          <TooltipTrigger asChild>
            <Badge variant="destructive" className="gap-1">
              <AlertTriangle className="size-3" />
              NMR
            </Badge>
          </TooltipTrigger>
          <TooltipContent>
            No Move Received — you did not submit orders in the previous phase
          </TooltipContent>
        </Tooltip>
      )}
      {cdBadge}
      {isFinished && resultBadge}
      {gunboatBadge}
      {isActive && game.isPaused && (
        <span className="inline-flex items-center gap-1 text-xs font-medium text-red-600">
          <Pause className="size-3.5" />
          Paused
        </span>
      )}
    </div>
  );

  const unreadPill = !game.sandbox &&
    (isActive || isFinished) &&
    game.totalUnreadMessageCount > 0 && (
      <Badge variant="default" className="gap-1">
        <Mail className="size-3" />
        <span className="relative top-px">{game.totalUnreadMessageCount} new</span>
      </Badge>
    );

  return (
    <Card className="w-full flex flex-col md:flex-row overflow-hidden p-0">
      <button
        onClick={handleClickGame}
        className="relative shrink-0 w-full h-40 md:h-auto md:w-48 md:self-stretch md:min-h-[150px] overflow-hidden cursor-pointer hover:opacity-90 transition-opacity"
        aria-label="Open game map"
      >
        {map}
      </button>

      <div className="flex flex-col flex-grow gap-2 p-4 min-w-0">
        <CardHeader className="p-0 gap-2">
          <div className="flex items-center justify-between gap-2">
            <button
              onClick={handleClickGame}
              className="text-left hover:underline min-w-0"
            >
              <CardTitle className="flex items-center gap-2 min-w-0">
                <span className="truncate">{game.name}</span>
                {game.sandbox && <Badge variant="secondary">Sandbox</Badge>}
                {!game.sandbox && (isActive || isFinished) && (
                  <NationBadge nations={variant.nations} nation={playerNation} />
                )}
              </CardTitle>
            </button>
            <div className="flex items-center gap-2 shrink-0">
              {unreadPill}
              {joinGameButton}
              <GameDropdownMenu
                game={game}
                onNavigateToGameInfo={handleClickGameInfo}
                onNavigateToPlayerInfo={handleClickPlayerInfo}
              />
            </div>
          </div>

          <CardDescription className="text-sm text-muted-foreground">
            <div className="flex items-center gap-1">
              {game.private && <Lock className="h-3 w-3" />}
              <span>
                {variant.name} •{" "}
                {game.sandbox
                  ? "Resolve when ready"
                  : game.deadlineMode === "fixed_time"
                  ? ({ hourly: "Hourly", daily: "Daily", every_2_days: "Every 2 days", weekly: "Weekly" }[game.movementFrequency ?? ""] ?? "Fixed time")
                  : (game.movementPhaseDuration || "Resolve when ready")}
              </span>
            </div>
            {isPending ? (
              <p>Created {formatTimeAgo(game.createdAt)}</p>
            ) : phase ? (
              <p className="flex items-center gap-1">
                <span>
                  {phase.season} {phase.year} • {phase.type}
                </span>
                {isActive &&
                  !game.sandbox &&
                  phase.status === "active" &&
                  phase.scheduledResolution &&
                  !game.isPaused && (
                    <>
                      <span>•</span>
                      <RemainingTimeDisplay
                        remainingTime={phase.remainingTime}
                        scheduledResolution={phase.scheduledResolution}
                        isPaused={game.isPaused}
                      />
                    </>
                  )}
              </p>
            ) : isFinished ? null : (
              <Skeleton className="w-24 h-4" />
            )}
          </CardDescription>
        </CardHeader>

        {!game.sandbox && (isActive || isFinished) && badgeCluster}

        <div className="flex-grow" />

        {showAvatars && (
          <CardFooter className="p-0 flex-col items-stretch gap-2">
            <div className="flex items-center justify-between gap-2">
              <button
                onClick={handleClickPlayerInfo}
                className="flex items-center gap-2"
              >
                {game.gameMaster && (
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Avatar className="h-8 w-8 border-2 border-background ring-2 ring-amber-400">
                        <AvatarImage src={game.gameMaster.picture ?? undefined} />
                        <AvatarFallback>
                          {game.gameMaster.name?.[0]?.toUpperCase() ?? "?"}
                        </AvatarFallback>
                      </Avatar>
                    </TooltipTrigger>
                    <TooltipContent>Game Master</TooltipContent>
                  </Tooltip>
                )}
                <div className="flex -space-x-2">
                  {game.members.slice(0, 7).map(member => (
                    <Avatar
                      key={member.id}
                      className={`h-8 w-8 border-2 border-background ${
                        isFinished && winnerIds.has(member.id)
                          ? "ring-2 ring-amber-400"
                          : ""
                      }`}
                    >
                      <AvatarImage src={member.picture ?? undefined} />
                      <AvatarFallback>
                        {member.name?.[0]?.toUpperCase() ?? "?"}
                      </AvatarFallback>
                    </Avatar>
                  ))}
                  {game.members.length > 7 && (
                    <div className="h-8 w-8 rounded-full bg-muted border-2 border-background flex items-center justify-center text-xs">
                      +{game.members.length - 7}
                    </div>
                  )}
                </div>
              </button>
              {isPending && totalSlots > 0 && (
                <span className="flex items-center gap-1 text-xs text-muted-foreground">
                  <Users className="size-3.5" />
                  {joinedCount}/{totalSlots} joined
                </span>
              )}
            </div>
            {isPending && totalSlots > 0 && (
              <div className="h-1.5 w-full rounded-full bg-secondary overflow-hidden">
                <div
                  className="h-full rounded-full bg-primary/80"
                  style={{
                    width: `${Math.round((joinedCount / totalSlots) * 100)}%`,
                  }}
                />
              </div>
            )}
          </CardFooter>
        )}
      </div>
    </Card>
  );
};

export { GameCard };
