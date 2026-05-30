import React from "react";
import { useNavigate } from "react-router";
import { toast } from "sonner";
import { useQueryClient } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { Variant } from "../api/generated/endpoints";
import { Card } from "@/components/ui/card";
import { GameDropdownMenu } from "./GameDropdownMenu";
import { Check, Clock, Lock, Mail, UserPlus, Users } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { RemainingTimeDisplay } from "./RemainingTimeDisplay";
import {
  GameList,
  MyOrderStatus,
  useGameJoinCreate,
  getGamesListQueryKey,
} from "../api/generated/endpoints";
import { formatTimeAgo, getGameLandingPath } from "../util";
import { Tooltip, TooltipContent, TooltipTrigger } from "./ui/tooltip";
import { useIsMobile } from "@/hooks/use-mobile";
import { useCheckNotificationPermission } from "@/hooks/useCheckNotificationPermission";

export interface GameCardProps {
  game: GameList;
  variant: Pick<Variant, "name" | "id" | "nations" | "templatePhase">;
  map: (focusProvinceIds?: string[]) => React.ReactNode;
  className?: string;
}

const orderStatusText = (status: MyOrderStatus): string => {
  if (status.submitted === 0) return "Orders pending";
  const fraction =
    status.total != null
      ? `${status.submitted}/${status.total} orders`
      : `${status.submitted} orders`;
  return fraction;
};

const GameCard: React.FC<GameCardProps> = ({ game, variant, map }) => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const isMobile = useIsMobile();
  const phase = game.currentPhase;
  const joinGameMutation = useGameJoinCreate();
  const checkNotificationPermission = useCheckNotificationPermission();

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

  const myMember = game.members.find(m => m.isCurrentUser);
  const isActiveMember =
    game.status === "active" && myMember != null && !game.sandbox;
  const isPending = game.status === "pending";

  const focusProvinceIds = myMember?.nation
    ? variant.templatePhase.units
        .filter(u => u.nation.name === myMember.nation)
        .map(u => u.province.id)
    : undefined;
  const totalSlots = variant.nations.length;

  const cadenceLabel = game.sandbox
    ? "Resolve when ready"
    : game.deadlineMode === "fixed_time"
    ? ({
        hourly: "Hourly",
        daily: "Daily",
        every_2_days: "Every 2 days",
        weekly: "Weekly",
      }[game.movementFrequency ?? ""] ?? "Fixed time")
    : game.movementPhaseDuration ?? "Resolve when ready";

  return (
    <Card className="w-full flex flex-col md:flex-row overflow-hidden p-0">
      {/* Map thumbnail */}
      <button
        onClick={handleClickGame}
        className="shrink-0 overflow-hidden w-full h-[150px] md:w-[196px] md:h-auto cursor-pointer hover:opacity-90 transition-opacity"
        style={{ aspectRatio: "1524/1357" }}
        aria-label="Open game"
      >
        {map(focusProvinceIds)}
      </button>

      {/* Content column */}
      <div className="flex flex-col flex-grow p-4 gap-2 min-w-0">

        {/* Title row */}
        <div className="flex items-center justify-between gap-2">
          <button
            onClick={handleClickGame}
            className="text-left hover:underline min-w-0 flex-1"
          >
            <span className="text-[18px] font-semibold leading-tight line-clamp-1 flex items-center gap-2">
              {game.name}
              {game.sandbox && (
                <Badge variant="secondary" className="shrink-0">Sandbox</Badge>
              )}
            </span>
          </button>
          <div className="flex items-center gap-1.5 shrink-0">
            {game.unreadMessageCount > 0 && (
              <span className="flex items-center gap-1 rounded-full bg-primary px-2 py-0.5 text-[11px] font-semibold text-primary-foreground whitespace-nowrap">
                <Mail className="size-3" strokeWidth={2.2} />
                {game.unreadMessageCount} new
              </span>
            )}
            {game.canJoin && (
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    onClick={handleJoinGame}
                    variant="outline"
                    size="icon"
                    aria-label="Join game"
                  >
                    <UserPlus className="size-4" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent>
                  <p>Join game</p>
                </TooltipContent>
              </Tooltip>
            )}
            <GameDropdownMenu
              game={game}
              onNavigateToGameInfo={handleClickGameInfo}
              onNavigateToPlayerInfo={handleClickPlayerInfo}
            />
          </div>
        </div>

        {/* Meta line 1: variant + cadence */}
        <div className="flex items-center gap-1.5 text-sm text-muted-foreground">
          {game.private && <Lock className="size-3 shrink-0" />}
          <span>{variant.name} • {cadenceLabel}</span>
        </div>

        {/* Meta line 2: phase info */}
        <div className="text-sm text-muted-foreground">
          {isPending ? (
            <span>Created {formatTimeAgo(game.createdAt)}</span>
          ) : phase ? (
            <span>
              {phase.season} {phase.year}
              <span className="opacity-50"> • </span>
              {phase.type}
            </span>
          ) : null}
        </div>

        {/* Spacer */}
        <div className="flex-1" />

        {/* Footer: active member game */}
        {isActiveMember && (
          <div className="flex items-center justify-between flex-wrap gap-2 border-t pt-2.5">
            {/* Country chip */}
            {myMember.nation && (
              <Badge
                variant="outline"
                className="rounded-full gap-1.5 text-xs font-medium px-2.5 py-1"
              >
                <span
                  className="size-2.5 rounded-sm shrink-0 inline-block"
                  style={{
                    background: myMember.nationColor ?? "#888",
                    boxShadow: "inset 0 0 0 1px rgb(0 0 0 / 0.12)",
                  }}
                />
                {myMember.nation}
              </Badge>
            )}

            {/* Time left + order status */}
            <div className="flex items-center gap-2.5 text-sm text-muted-foreground">
              {phase?.status === "active" && phase.scheduledResolution && (
                <span className="flex items-center gap-1">
                  <Clock className="size-3 shrink-0" />
                  <RemainingTimeDisplay
                    remainingTime={phase.remainingTime}
                    scheduledResolution={phase.scheduledResolution}
                    isPaused={game.isPaused}
                  />
                </span>
              )}
              {game.myOrderStatus && (
                <span className="flex items-center gap-1 whitespace-nowrap">
                  {orderStatusText(game.myOrderStatus)}
                  {game.myOrderStatus.confirmed && (
                    <Check className="size-3.5 text-emerald-500 shrink-0" />
                  )}
                </span>
              )}
            </div>
          </div>
        )}

        {/* Footer: pending game */}
        {isPending && !game.sandbox && (
          <div className="flex flex-col gap-2 border-t pt-2.5">
            <div className="flex items-center justify-between">
              <button onClick={handleClickPlayerInfo} className="flex -space-x-2">
                {game.members.slice(0, 6).map(member => (
                  <Avatar
                    key={member.id}
                    className="h-8 w-8 border-2 border-background"
                  >
                    <AvatarImage src={member.picture ?? undefined} />
                    <AvatarFallback>
                      {member.name?.[0]?.toUpperCase() ?? "?"}
                    </AvatarFallback>
                  </Avatar>
                ))}
              </button>
              <span className="flex items-center gap-1.5 text-xs text-muted-foreground">
                <Users className="size-3" />
                {game.members.length}/{totalSlots} joined
              </span>
            </div>
            <div className="h-1.5 rounded-full bg-secondary overflow-hidden">
              <div
                className="h-full rounded-full bg-primary/80"
                style={{
                  width: `${Math.round((game.members.length / totalSlots) * 100)}%`,
                }}
              />
            </div>
          </div>
        )}

        {/* Footer: active non-member / sandbox / completed */}
        {!isActiveMember && !isPending && !game.sandbox && (
          <div className="border-t pt-2.5">
            <button onClick={handleClickPlayerInfo} className="flex -space-x-2">
              {game.members.slice(0, 7).map(member => (
                <Avatar
                  key={member.id}
                  className="h-8 w-8 border-2 border-background"
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
            </button>
          </div>
        )}
      </div>
    </Card>
  );
};

export { GameCard };
