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
import { NationFlag, findNationColor, findNationFlagUrl } from "./NationFlag";
import {
  UserPlus,
  Info,
  Lock,
  ShieldCheck,
  MessageSquareOff,
  Mail,
  Clock,
  Check,
  AlertTriangle,
  UserX,
  Pause,
  Skull,
  Trophy,
  Users,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { RemainingTimeDisplay } from "./RemainingTimeDisplay";
import {
  GameList,
  useGameMemberJoinCreate,
  useGameMusterCreate,
  getGamesListQueryKey,
} from "../api/generated/endpoints";
import { formatTimeAgo, getGameLandingPath } from "../util";
import { Skeleton } from "./ui/skeleton";
import { Tooltip, TooltipContent, TooltipTrigger } from "./ui/tooltip";
import { Popover, PopoverContent, PopoverTrigger } from "./ui/popover";
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

const MUSTER_STATUS_CONFIG: Record<
  string,
  { label: string; badgeClassName: string; icon: React.ReactNode; tooltip: string }
> = {
  confirmation_required: {
    label: "Confirmation required",
    badgeClassName: "bg-amber-500 text-white hover:bg-amber-500",
    icon: <Clock className="size-3" />,
    tooltip: "Confirm you're ready to play before the deadline or you'll lose your seat",
  },
  confirmed: {
    label: "Ready",
    badgeClassName: "bg-green-600 text-white hover:bg-green-600",
    icon: <Check className="size-3" />,
    tooltip: "You've confirmed — the game starts once every player is ready",
  },
};

const GameCard: React.FC<GameCardProps> = ({ game, variant, map }) => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const isMobile = useIsMobile();
  const phase = game.currentPhase;
  const members = Array.isArray(game.members) ? game.members : [];
  const playerNation = members.find(m => m.isCurrentUser)?.nation ?? null;
  const joinGameMutation = useGameMemberJoinCreate();
  const musterMutation = useGameMusterCreate();
  const checkNotificationPermission = useCheckNotificationPermission();

  const isActive = game.status === "active";
  const isPending = game.status === "pending";
  const isMustering = game.status === "mustering";
  const isAbandoned = game.status === "abandoned";
  const isFinished = game.status === "completed" || isAbandoned;
  const currentMember = members.find(m => m.isCurrentUser);
  const showAvatars = !game.sandbox;
  const totalSlots = variant.nations.length;
  const joinedCount = members.length;
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
      await joinGameMutation.mutateAsync({ gameId: game.id });
      toast.success("Successfully joined game");
      queryClient.invalidateQueries({ queryKey: getGamesListQueryKey() });
      if (!game.sandbox) {
        checkNotificationPermission();
      }
    } catch {
      toast.error("Failed to join game");
    }
  };

  const handleConfirmMuster = async () => {
    try {
      await musterMutation.mutateAsync({ gameId: game.id });
      toast.success("Seat confirmed");
      queryClient.invalidateQueries({ queryKey: getGamesListQueryKey() });
    } catch {
      toast.error("Failed to confirm seat");
    }
  };

  const isCommitmentLocked =
    game.commitmentEligibility === "committed_locked" ||
    game.commitmentEligibility === "low_locked";

  const lockedReason =
    game.commitmentEligibility === "low_locked"
      ? "Your commitment rating is Low, so you can't join games right now. Your rating is based on your last 10 rated phases."
      : "This game admits players with High commitment only. Submit orders on time in your games to raise your rating.";

  const joinGameButton =
    game.canJoin &&
    (isCommitmentLocked ? (
      <Button variant="outline" aria-label="Locked" disabled>
        <Lock className="size-4" />
      </Button>
    ) : (
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
    ));

  const confirmMusterButton = game.musterStatus === "confirmation_required" && (
    <Tooltip>
      <TooltipTrigger asChild>
        <Button onClick={handleConfirmMuster} aria-label="Confirm seat">
          <Check className="size-4" />
          Confirm
        </Button>
      </TooltipTrigger>
      <TooltipContent>
        <p>Confirm you're ready to play</p>
      </TooltipContent>
    </Tooltip>
  );

  const orderStatusConfig = game.orderStatus
    ? ORDER_STATUS_CONFIG[game.orderStatus]
    : undefined;

  const musterStatusConfig = game.musterStatus
    ? MUSTER_STATUS_CONFIG[game.musterStatus]
    : undefined;

  const gunboatIcon = game.pressType === "no_press" && (
    <Tooltip>
      <TooltipTrigger asChild>
        <MessageSquareOff
          className="size-4 shrink-0 text-muted-foreground"
          aria-label="Gunboat"
        />
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

  const badges = [
    game.sandbox && (
      <Badge key="sandbox" variant="secondary">
        Sandbox
      </Badge>
    ),
    isActive && !game.sandbox && currentMember?.eliminated && (
      <Tooltip key="eliminated">
        <TooltipTrigger asChild>
          <Badge variant="secondary" className="gap-1">
            <Skull className="size-3" />
            Eliminated
          </Badge>
        </TooltipTrigger>
        <TooltipContent>You have been eliminated from this game</TooltipContent>
      </Tooltip>
    ),
    isActive && orderStatusConfig && (
      <Tooltip key="order-status">
        <TooltipTrigger asChild>
          <Badge className={`gap-1 ${orderStatusConfig.badgeClassName}`}>
            {orderStatusConfig.icon}
            {orderStatusConfig.label}
          </Badge>
        </TooltipTrigger>
        <TooltipContent>{orderStatusConfig.tooltip}</TooltipContent>
      </Tooltip>
    ),
    isMustering && musterStatusConfig && (
      <Tooltip key="muster-status">
        <TooltipTrigger asChild>
          <Badge className={`gap-1 ${musterStatusConfig.badgeClassName}`}>
            {musterStatusConfig.icon}
            {musterStatusConfig.label}
          </Badge>
        </TooltipTrigger>
        <TooltipContent>{musterStatusConfig.tooltip}</TooltipContent>
      </Tooltip>
    ),
    isActive && game.memberStatus?.includes("nmr") && (
      <Tooltip key="nmr">
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
    ),
    cdBadge && <React.Fragment key="cd">{cdBadge}</React.Fragment>,
    isFinished && resultBadge && (
      <React.Fragment key="result">{resultBadge}</React.Fragment>
    ),
    isActive && game.isPaused && (
      <span
        key="paused"
        className="inline-flex items-center gap-1 text-xs font-medium text-red-600"
      >
        <Pause className="size-3.5" />
        Paused
      </span>
    ),
  ].filter(Boolean);

  const badgeCluster = badges.length > 0 && (
    <div className="flex flex-wrap items-center gap-2">{badges}</div>
  );

  const nationColor = findNationColor(variant.nations, playerNation);
  const nationFlagUrl = findNationFlagUrl(variant.nations, playerNation);

  const nationPill = !game.sandbox &&
    (isActive || isFinished) &&
    playerNation && (
      <div
        className="pointer-events-none absolute bottom-2 left-2 md:left-auto md:right-2 flex max-w-[calc(100%-1rem)] items-center gap-1.5 rounded-full border bg-background px-2 py-1"
        style={{ borderColor: nationColor ?? undefined }}
      >
        {nationFlagUrl ? (
          <NationFlag
            flagUrl={nationFlagUrl}
            size="sm"
            className="shrink-0 ring-1 ring-black/10"
          />
        ) : (
          <span
            className="size-4 shrink-0 rounded-full ring-1 ring-black/10"
            style={{ backgroundColor: nationColor ?? undefined }}
          />
        )}
        <span className="truncate text-xs font-medium">{playerNation}</span>
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
      <div className="relative shrink-0 w-full h-40 md:h-44 md:w-48">
        <button
          onClick={handleClickGame}
          className="relative w-full h-full overflow-hidden cursor-pointer hover:opacity-90 transition-opacity"
          aria-label="Open game map"
        >
          {map}
        </button>
        {nationPill}
      </div>

      <div className="flex flex-col flex-grow gap-2 p-4 md:py-2 min-w-0">
        <CardHeader className="p-0 gap-2">
          <div className="flex items-center justify-between gap-2">
            <div className="flex items-center min-w-0 gap-1">
              <button
                onClick={handleClickGame}
                className="text-left hover:underline min-w-0 overflow-hidden"
              >
                <CardTitle className="truncate">{game.name}</CardTitle>
              </button>
              {gunboatIcon}
            </div>
            <div className="flex items-center gap-2 shrink-0">
              {unreadPill}
              {joinGameButton}
              {confirmMusterButton}
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
            ) : isMustering ? (
              <p className="flex items-center gap-1">
                <span>Starts when every player confirms</span>
                {game.musterDeadline && (
                  <>
                    <span>•</span>
                    <RemainingTimeDisplay
                      remainingTime={Math.max(
                        0,
                        (new Date(game.musterDeadline).getTime() - Date.now()) /
                          1000
                      )}
                      scheduledResolution={game.musterDeadline}
                    />
                  </>
                )}
              </p>
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

          {isPending && game.commitmentRequirement === "committed" && !isCommitmentLocked && (
            <div>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Badge className="gap-1 bg-green-600">
                    <ShieldCheck className="size-3" />
                    Committed
                  </Badge>
                </TooltipTrigger>
                <TooltipContent>
                  Only players with High commitment can join this game
                </TooltipContent>
              </Tooltip>
            </div>
          )}

          {isPending && isCommitmentLocked && (
            <p className="flex items-center gap-1 text-xs text-muted-foreground">
              <Lock className="size-3" />
              {game.commitmentEligibility === "low_locked"
                ? "Locked: your commitment is Low"
                : "Locked: requires High commitment"}
              <Popover>
                <PopoverTrigger asChild>
                  <button
                    type="button"
                    className="text-muted-foreground/60 hover:text-muted-foreground"
                    aria-label="Why is this game locked?"
                  >
                    <Info className="size-3.5" />
                  </button>
                </PopoverTrigger>
                <PopoverContent className="text-sm">{lockedReason}</PopoverContent>
              </Popover>
            </p>
          )}
        </CardHeader>

        {badgeCluster}

        {showAvatars && (
          <CardFooter className="p-0 mt-auto flex-col items-stretch gap-2">
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
                  {members.slice(0, 7).map(member => (
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
                  {members.length > 7 && (
                    <div className="h-8 w-8 rounded-full bg-muted border-2 border-background flex items-center justify-center text-xs">
                      +{members.length - 7}
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
