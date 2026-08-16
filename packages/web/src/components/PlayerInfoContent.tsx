import React, { useState } from "react";
import {
  Bot,
  MessageCircle,
  Shield,
  Star,
  Swords,
  Trophy,
  User,
  UserPlus,
  X,
} from "lucide-react";
import { Link, useNavigate, useParams } from "react-router";
import { toast } from "sonner";
import { useQueryClient } from "@tanstack/react-query";

import { AddBotSheet } from "@/components/AddBotSheet";
import { CivilDisorderBadge } from "@/components/CivilDisorderBadge";
import { CommitmentBadge } from "@/components/CommitmentBadge";
import { GameStatusAlerts } from "@/components/GameStatusAlerts";
import { NationFlag, findNationFlagUrl, findNationColor } from "@/components/NationFlag";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { ScreenCard, ScreenCardContent } from "@/components/ui/screen-card";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import {
  useGameRetrieveSuspense,
  useGamePhaseRetrieve,
  useGameKickDestroy,
  useUserRetrieveSuspense,
  getGameAddableUserListQueryKey,
  getGamesChannelsListQueryKey,
  getGameRetrieveQueryKey,
  useGamesChannelsCreateCreate,
  useGamesChannelsList,
  type Channel,
  Member,
} from "@/api/generated/endpoints";
import { useGameVariant } from "@/hooks/useGameVariant";
import { getCurrentPhaseId } from "@/util";
import { useRequiredParams } from "@/hooks";
import { useIsMobile } from "@/hooks/use-mobile";

export const PlayerInfoContent: React.FC = () => {
  const { gameId } = useRequiredParams<{ gameId: string }>();
  const { phaseId } = useParams<{ phaseId: string }>();
  const navigate = useNavigate();
  const isMobile = useIsMobile();

  const { data: game } = useGameRetrieveSuspense(gameId);
  const variant = useGameVariant(game);
  const { data: userProfile } = useUserRetrieveSuspense();
  const queryClient = useQueryClient();
  const kickMutation = useGameKickDestroy();
  const createChannelMutation = useGamesChannelsCreateCreate();

  const [addBotOpen, setAddBotOpen] = useState(false);

  const currentPhaseId = getCurrentPhaseId(game);
  const { data: currentPhase } = useGamePhaseRetrieve(
    gameId,
    currentPhaseId ?? 0,
    { query: { enabled: !!currentPhaseId } }
  );

  const currentMember = game.members.find(member => member.isCurrentUser);
  const isNoPressActiveGame =
    game.pressType === "no_press" &&
    game.status !== "completed" &&
    game.status !== "abandoned";
  const canUseChat =
    !!phaseId && !!currentMember && !game.sandbox && !isNoPressActiveGame;
  const channelsQuery = useGamesChannelsList(gameId, {
    query: { enabled: canUseChat },
  });

  const getDirectChannel = (member: Member) =>
    channelsQuery.data?.find(channel => {
      const memberIds = channel.memberIds ?? [];
      return (
        channel.private &&
        memberIds.length === 2 &&
        !!currentMember &&
        memberIds.includes(currentMember.id) &&
        memberIds.includes(member.id)
      );
    });

  const getSupplyCenterCount = (member: Member) => {
    if (!currentPhase) return undefined;
    return currentPhase.supplyCenters.filter(
      sc => sc.nation.name === member.nation
    ).length;
  };

  const getUnitCount = (member: Member) => {
    if (!currentPhase) return undefined;
    return currentPhase.units.filter(unit => unit.nation.name === member.nation)
      .length;
  };

  const winnerIds = game.victory?.members?.map(m => m.id) || [];

  const isPending = game.status === "pending";
  const playableSeats = variant
    ? variant.nations.filter(n => !n.nonPlayable).length
    : 0;
  const openSeats = isPending
    ? Math.max(0, playableSeats - game.members.length)
    : 0;
  const canAddBots =
    isPending && game.canManage && userProfile.canCreateBotGames;
  const sortedMembers = [...game.members].sort((a, b) => {
    if (game.status === "completed") {
      const winnerOrder =
        Number(winnerIds.includes(b.id)) - Number(winnerIds.includes(a.id));
      if (winnerOrder !== 0) return winnerOrder;
    }

    return (
      Number(!!a.eliminated || !!a.civilDisorder) -
      Number(!!b.eliminated || !!b.civilDisorder)
    );
  });

  const handleRemoveBot = async (member: Member) => {
    try {
      await kickMutation.mutateAsync({ gameId, memberId: member.id });
      await Promise.all([
        queryClient.invalidateQueries({
          queryKey: getGameRetrieveQueryKey(gameId),
        }),
        queryClient.invalidateQueries({
          queryKey: getGameAddableUserListQueryKey(gameId),
        }),
      ]);
      toast.success(`${member.name} removed from the game`);
    } catch {
      toast.error("Failed to remove AI player");
    }
  };

  const handleOpenChat = async (member: Member) => {
    if (!phaseId || !currentMember) return;

    const existingChannel = getDirectChannel(member);

    if (existingChannel) {
      navigate(
        `/game/${gameId}/phase/${phaseId}/chat/channel/${existingChannel.id}`
      );
      return;
    }

    try {
      const channel = await createChannelMutation.mutateAsync({
        gameId,
        data: { memberIds: [member.id] },
      });
      queryClient.setQueryData<Channel[]>(
        getGamesChannelsListQueryKey(gameId),
        old => [...(old ?? []), channel]
      );
      navigate(`/game/${gameId}/phase/${phaseId}/chat/channel/${channel.id}`);
    } catch {
      toast.error("Failed to open chat");
    }
  };

  return (
    <>
      <GameStatusAlerts game={game} variant={variant} />

      <ScreenCard>
        <ScreenCardContent className="divide-y">
          {game.gameMaster && (
            <div className="flex items-center gap-4 py-4 first:pt-0 last:pb-0">
              <Avatar className="size-8">
                <AvatarImage src={game.gameMaster.picture ?? undefined} />
                <AvatarFallback>
                  {game.gameMaster.name[0]?.toUpperCase() ?? "?"}
                </AvatarFallback>
              </Avatar>
              <div className="flex items-center gap-2 flex-wrap">
                <Link
                  to={`/player/${game.gameMaster.userId}`}
                  className="font-medium text-primary underline-offset-4 hover:underline"
                >
                  {game.gameMaster.name}
                </Link>
                <Badge variant="secondary" className="gap-1">
                  <Shield className="size-3" />
                  Game Master
                </Badge>
              </div>
            </div>
          )}
          {sortedMembers.map(member => {
            const supplyCenterCount = getSupplyCenterCount(member);
            const unitCount = getUnitCount(member);
            const isWinner = winnerIds.includes(member.id);
            const flagUrl = variant
              ? findNationFlagUrl(variant.nations, member.nation)
              : null;
            const nationColor = variant
              ? findNationColor(variant.nations, member.nation)
              : null;
            const showChatShortcut =
              canUseChat &&
              !member.isCurrentUser &&
              !member.isBot &&
              !member.kicked;
            const directChannel = showChatShortcut
              ? getDirectChannel(member)
              : undefined;
            const unreadMessageCount = directChannel?.unreadMessageCount ?? 0;
            const showNationFocusedLayout = !!phaseId && !!member.nation;

            return (
              <div
                key={member.id}
                className={`flex items-center gap-4 py-4 first:pt-0 last:pb-0 ${
                  member.eliminated || member.civilDisorder
                    ? "opacity-[0.7]"
                    : ""
                }`}
              >
                {member.nation &&
                  variant &&
                  (flagUrl ? (
                    <NationFlag
                      flagUrl={flagUrl}
                      alt={member.nation}
                      size="lg"
                      className="size-8"
                      color={nationColor}
                    />
                  ) : (
                    <span
                      role="img"
                      aria-label={`${member.nation} colour`}
                      className="size-8 shrink-0 rounded-full border"
                      style={{ backgroundColor: nationColor ?? undefined }}
                    />
                  ))}

                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    {showNationFocusedLayout ? (
                      <span className="font-medium">{member.nation}</span>
                    ) : member.userId ? (
                      <Link
                        to={`/player/${member.userId}`}
                        className="font-medium text-primary underline-offset-4 hover:underline"
                      >
                        {member.name}
                      </Link>
                    ) : (
                      <span className="font-medium">{member.name}</span>
                    )}
                    {member.isBot && (
                      <Badge variant="secondary" className="gap-1">
                        <Bot className="size-3" />
                        Bot
                      </Badge>
                    )}
                    {!showNationFocusedLayout &&
                      !member.isBot &&
                      member.commitment && (
                        <CommitmentBadge commitment={member.commitment} />
                      )}
                    {member.isGameCreator && (
                      <Badge variant="secondary" className="gap-1">
                        <Shield className="size-3" />
                        Game Creator
                      </Badge>
                    )}
                    {isWinner && (
                      <Badge variant="default" className="gap-1">
                        <Trophy className="size-3" />
                        {game.victory?.type === "solo" ? "Winner" : "Draw"}
                      </Badge>
                    )}
                    {member.eliminated ? (
                      <Badge variant="secondary">Eliminated</Badge>
                    ) : (
                      member.civilDisorder && <CivilDisorderBadge />
                    )}
                  </div>

                  {member.nation && (
                    <div className="text-sm text-muted-foreground mt-1">
                      <span className="inline-flex items-center gap-2">
                        {!showNationFocusedLayout && (
                          <>
                            <span>{member.nation}</span>
                            <span>•</span>
                          </>
                        )}
                        <span className="inline-flex items-center gap-1">
                          <Swords className="size-3" />
                          {unitCount !== undefined ? (
                            <span>{unitCount} units</span>
                          ) : (
                            <Skeleton className="h-3 w-10" />
                          )}
                        </span>
                        <span>•</span>
                        <span className="inline-flex items-center gap-1">
                          <Star className="size-3" />
                          {supplyCenterCount !== undefined ? (
                            <span>{supplyCenterCount} centers</span>
                          ) : (
                            <Skeleton className="h-3 w-12" />
                          )}
                        </span>
                      </span>
                    </div>
                  )}
                </div>

                {showNationFocusedLayout && (
                  <div className="flex shrink-0 items-center">
                    {showChatShortcut && (
                      <Button
                        variant="ghost"
                        size="icon"
                        className="relative"
                        aria-label={
                          unreadMessageCount > 0
                            ? `Message ${member.name}, ${unreadMessageCount} unread ${
                                unreadMessageCount === 1
                                  ? "message"
                                  : "messages"
                              }`
                            : `Message ${member.name}`
                        }
                        disabled={
                          channelsQuery.isLoading ||
                          createChannelMutation.isPending
                        }
                        onClick={() => handleOpenChat(member)}
                      >
                        <MessageCircle className="size-4" />
                        {unreadMessageCount > 0 && (
                          <span
                            aria-hidden="true"
                            className="absolute right-1.5 top-1.5 size-2 rounded-full bg-primary ring-2 ring-background"
                          />
                        )}
                      </Button>
                    )}

                    <Popover>
                      <PopoverTrigger asChild>
                        <Button
                          variant="ghost"
                          size="icon"
                          aria-label={`View ${member.nation} player details`}
                        >
                          <User className="size-4" />
                        </Button>
                      </PopoverTrigger>
                      <PopoverContent
                        side={isMobile ? "left" : "right"}
                        align="center"
                        sideOffset={8}
                        collisionPadding={8}
                        className="w-max max-w-[calc(100vw-1rem)] p-3"
                      >
                        <div className="space-y-1">
                          <div className="flex items-center gap-2">
                            {member.userId ? (
                              <Link
                                to={`/game/${gameId}/phase/${phaseId}/player/${member.userId}`}
                                className="whitespace-nowrap font-medium text-primary underline-offset-4 hover:underline"
                              >
                                {member.name}
                              </Link>
                            ) : (
                              <p className="whitespace-nowrap font-medium">
                                {member.name}
                              </p>
                            )}
                            {!member.isBot && member.commitment && (
                              <CommitmentBadge commitment={member.commitment} />
                            )}
                          </div>
                          {game.nmrExtensionsAllowed > 0 && (
                            <p className="whitespace-nowrap text-sm text-muted-foreground">
                              {member.nmrExtensionsRemaining}{" "}
                              {member.nmrExtensionsRemaining === 1
                                ? "extension"
                                : "extensions"}{" "}
                              remaining
                            </p>
                          )}
                        </div>
                      </PopoverContent>
                    </Popover>
                  </div>
                )}

                {!showNationFocusedLayout && showChatShortcut && (
                  <Button
                    variant="ghost"
                    size="icon"
                    aria-label={`Message ${member.name}`}
                    disabled={
                      channelsQuery.isLoading || createChannelMutation.isPending
                    }
                    onClick={() => handleOpenChat(member)}
                  >
                    <MessageCircle className="size-4" />
                  </Button>
                )}

                {isPending && game.canManage && member.isBot && (
                  <Button
                    variant="ghost"
                    size="icon"
                    aria-label={`Remove ${member.name}`}
                    disabled={kickMutation.isPending}
                    onClick={() => handleRemoveBot(member)}
                  >
                    <X className="size-4" />
                  </Button>
                )}
              </div>
            );
          })}
          {Array.from({ length: openSeats }, (_, index) =>
            canAddBots ? (
              <button
                key={`open-seat-${index}`}
                onClick={() => setAddBotOpen(true)}
                className="flex items-center gap-4 py-4 first:pt-0 last:pb-0 w-full text-left"
              >
                <div className="size-8 rounded-full border border-dashed border-muted-foreground/50 flex items-center justify-center">
                  <UserPlus className="size-4 text-muted-foreground" />
                </div>
                <span className="font-medium text-primary underline-offset-4 hover:underline">
                  Add AI player
                </span>
              </button>
            ) : (
              <div
                key={`open-seat-${index}`}
                className="flex items-center gap-4 py-4 first:pt-0 last:pb-0"
              >
                <div className="size-8 rounded-full border border-dashed border-muted-foreground/50" />
                <span className="text-muted-foreground">Open seat</span>
              </div>
            )
          )}
        </ScreenCardContent>
      </ScreenCard>

      {canAddBots && (
        <AddBotSheet
          gameId={gameId}
          open={addBotOpen && openSeats > 0}
          onOpenChange={setAddBotOpen}
        />
      )}
    </>
  );
};
