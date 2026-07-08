import React, { useState } from "react";
import { toast } from "sonner";
import { useQueryClient } from "@tanstack/react-query";
import { BookOpen, Calendar, Clock, Users, Lock, Unlock, User, Map, Trophy, Pause, Shield, ShieldCheck, MessageSquare, MessageSquareOff, Bot, Share } from "lucide-react";

import { Skeleton } from "@/components/ui/skeleton";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { GameStatusAlerts } from "@/components/GameStatusAlerts";
import { DeadlineSummary } from "@/components/DeadlineSummary";
import { AddBotSheet } from "@/components/AddBotSheet";
import {
  useGameRetrieveSuspense,
  useGameJoinCreate,
  useGameLeaveDestroy,
  useUserRetrieveSuspense,
  getGameRetrieveQueryKey,
} from "@/api/generated/endpoints";
import { useGameVariant } from "@/hooks/useGameVariant";
import { useCheckNotificationPermission } from "@/hooks/useCheckNotificationPermission";
import { formatDateTime, formatTimeAgo } from "@/util";
import { MIN_RELIABILITY_OPTIONS } from "@/constants";
import { CardTitle } from "@/components/ui/card";
import {
  ScreenCard,
  ScreenCardContent,
  ScreenCardHeader,
} from "@/components/ui/screen-card";
import { useRequiredParams } from "@/hooks";

interface MetadataRowProps {
  icon: React.ReactNode;
  label: string;
  value: React.ReactNode;
}

const MetadataRow: React.FC<MetadataRowProps> = ({ icon, label, value }) => {
  return (
    <div className="flex items-center justify-between py-3 px-2">
      <div className="flex items-center gap-3">
        <div className="text-muted-foreground">{icon}</div>
        <span className="text-sm">{label}</span>
      </div>
      <div className="text-sm text-muted-foreground">{value}</div>
    </div>
  );
};

interface MetadataTextRowProps {
  icon: React.ReactNode;
  label: string;
  text: string;
}

const MetadataTextRow: React.FC<MetadataTextRowProps> = ({ icon, label, text }) => {
  return (
    <div className="py-3 px-2">
      <div className="flex items-center gap-3 mb-1">
        <div className="text-muted-foreground">{icon}</div>
        <span className="text-sm">{label}</span>
      </div>
      <p className="text-sm text-muted-foreground whitespace-pre-line pl-7">{text}</p>
    </div>
  );
};

interface GameInfoContentProps {
  onNavigateToPlayerInfo: () => void;
}

export const GameInfoContent: React.FC<GameInfoContentProps> = ({
  onNavigateToPlayerInfo,
}) => {
  const { gameId } = useRequiredParams<{ gameId: string }>();

  const queryClient = useQueryClient();
  const { data: game } = useGameRetrieveSuspense(gameId);
  const variant = useGameVariant(game);
  const { data: userProfile } = useUserRetrieveSuspense();
  const joinGameMutation = useGameJoinCreate();
  const leaveGameMutation = useGameLeaveDestroy();
  const checkNotificationPermission = useCheckNotificationPermission();

  const [addBotOpen, setAddBotOpen] = useState(false);

  const handleJoinGame = async () => {
    try {
      await joinGameMutation.mutateAsync({ gameId, data: {} });
      await queryClient.invalidateQueries({ queryKey: getGameRetrieveQueryKey(gameId) });
      toast.success("Game joined successfully");
      if (!game.sandbox) {
        checkNotificationPermission();
      }
    } catch {
      toast.error("Failed to join game");
    }
  };

  const handleLeaveGame = async () => {
    try {
      await leaveGameMutation.mutateAsync({ gameId });
      await queryClient.invalidateQueries({ queryKey: getGameRetrieveQueryKey(gameId) });
      toast.success("Game left successfully");
    } catch {
      toast.error("Failed to leave game");
    }
  };

  const handleShare = async () => {
    try {
      await navigator.clipboard.writeText(`https://diplicity.com/game/${gameId}`);
      toast.success("Link copied to clipboard");
    } catch {
      toast.error("Failed to copy link");
    }
  };

  const playableSeats = variant
    ? variant.nations.filter(n => !n.nonPlayable).length
    : 0;
  const openSeats = Math.max(0, playableSeats - game.members.length);
  const canAddBots =
    game.status === "pending" &&
    game.canManage &&
    userProfile.canCreateBotGames &&
    openSeats > 0;

  const pendingAction = game.status === "pending" ? (
    game.canJoin ? (
      <Button
        onClick={handleJoinGame}
        disabled={joinGameMutation.isPending}
        className="w-full @[500px]:w-auto"
      >
        Join game
      </Button>
    ) : game.canLeave || canAddBots ? (
      <div className="flex flex-wrap gap-2 w-full @[500px]:w-auto">
        {canAddBots && (
          <Button
            onClick={() => setAddBotOpen(true)}
            className="flex-1 @[500px]:flex-none"
          >
            <Bot className="size-4" />
            Add AI player
          </Button>
        )}
        {game.canLeave && (
          <Button
            onClick={handleLeaveGame}
            disabled={leaveGameMutation.isPending}
            variant="outline"
            className="flex-1 @[500px]:flex-none"
          >
            Leave
          </Button>
        )}
        <Button variant="outline" className="flex-1 @[500px]:flex-none" onClick={handleShare}>
          <Share className="size-4" />
          Share &amp; invite
        </Button>
      </div>
    ) : game.minReliability !== "open" ? (
      <div className="flex flex-col gap-1 w-full @[500px]:w-auto">
        <Button disabled className="w-full @[500px]:w-auto">
          Join game
        </Button>
        <p className="text-xs text-muted-foreground text-center">
          Your reliability is too low to join this game
        </p>
      </div>
    ) : null
  ) : null;

  return (
    <>
      <GameStatusAlerts game={game} variant={variant} action={pendingAction} />
      <ScreenCard>
        <ScreenCardHeader>
          <CardTitle>{game.name}</CardTitle>
        </ScreenCardHeader>
        <ScreenCardContent>
          <MetadataRow
            icon={<Map className="size-4" />}
            label="Variant"
            value={variant?.name ?? <Skeleton className="h-4 w-24" />}
          />
          {variant?.description && (
            <MetadataTextRow
              icon={<Map className="size-4" />}
              label="Description"
              text={variant.description}
            />
          )}
          <MetadataRow
            icon={<Clock className="size-4" />}
            label="Created"
            value={formatTimeAgo(game.createdAt)}
          />
          <div className="py-3 px-2">
            <div className="flex items-center gap-3 mb-1">
              <div className="text-muted-foreground"><Calendar className="size-4" /></div>
              <span className="text-sm">Phase deadlines</span>
            </div>
            <div className="text-sm text-muted-foreground pl-7">
              <DeadlineSummary game={game} />
            </div>
          </div>
          <MetadataRow
            icon={
              game.private ? (
                <Lock className="size-4" />
              ) : (
                <Unlock className="size-4" />
              )
            }
            label="Visibility"
            value={game.private ? "Private" : "Public"}
          />
          <MetadataRow
            icon={
              game.pressType === "no_press" ? (
                <MessageSquareOff className="size-4" />
              ) : (
                <MessageSquare className="size-4" />
              )
            }
            label="Press type"
            value={game.pressType === "no_press" ? "No Press" : "Full Press"}
          />
          {game.status === "completed" && game.victory && (
            <MetadataRow
              icon={<Trophy className="size-4" />}
              label={game.victory.type === "solo" ? "Winner" : "Draw"}
              value={game.victory.members.map(m => m.name).join(", ")}
            />
          )}
          {game.isPaused && game.pausedAt && (
            <MetadataRow
              icon={<Pause className="size-4" />}
              label="Paused since"
              value={formatDateTime(game.pausedAt)}
            />
          )}
          {game.nmrExtensionsAllowed > 0 && (
            <MetadataRow
              icon={<Shield className="size-4" />}
              label="NMR extensions"
              value={`${game.nmrExtensionsAllowed} per player`}
            />
          )}
          <MetadataRow
            icon={<ShieldCheck className="size-4" />}
            label="Player reliability"
            value={
              MIN_RELIABILITY_OPTIONS.find(o => o.value === game.minReliability)?.label ??
              game.minReliability
            }
          />
          <MetadataRow
            icon={<Users className="size-4" />}
            label="Players"
            value={
              variant ? (
                <button
                  onClick={onNavigateToPlayerInfo}
                  className="flex -space-x-2"
                >
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
              ) : (
                <Skeleton className="h-8 w-24" />
              )
            }
          />
          <MetadataRow
            icon={<Users className="size-4" />}
            label="Number of nations"
            value={
              variant?.nations.length.toString() ?? (
                <Skeleton className="h-4 w-8" />
              )
            }
          />
          <MetadataRow
            icon={<Calendar className="size-4" />}
            label="Start year"
            value={
              variant?.templatePhase.year?.toString() ?? (
                <Skeleton className="h-4 w-12" />
              )
            }
          />
          <MetadataRow
            icon={<User className="size-4" />}
            label="Original author"
            value={variant?.author ?? <Skeleton className="h-4 w-24" />}
          />
          {variant?.rules && (
            <MetadataTextRow
              icon={<BookOpen className="size-4" />}
              label="Rules"
              text={variant.rules}
            />
          )}
        </ScreenCardContent>
      </ScreenCard>
      {canAddBots && (
        <AddBotSheet
          gameId={gameId}
          open={addBotOpen}
          onOpenChange={setAddBotOpen}
        />
      )}
    </>
  );
};
