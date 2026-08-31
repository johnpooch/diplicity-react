import React, { useState } from "react";
import {
  Bot,
  ChevronRight,
  Link2,
  MessageCircle,
  MoreVertical,
  Shield,
  Star,
  Swords,
  Trophy,
  User,
  UserMinus,
  UserPlus,
} from "lucide-react";
import { Link, useNavigate, useParams } from "react-router";
import { toast } from "sonner";
import { useQueryClient } from "@tanstack/react-query";

import { AddBotSheet } from "@/components/AddBotSheet";
import { CivilDisorderBadge } from "@/components/CivilDisorderBadge";
import { CommitmentBadge } from "@/components/CommitmentBadge";
import { GameStatusAlerts } from "@/components/GameStatusAlerts";
import { NationAssignmentAlert } from "@/components/NationAssignmentAlert";
import { KickedBadge } from "@/components/KickedBadge";
import {
  NationFlag,
  findNationFlagUrl,
  findNationColor,
} from "@/components/NationFlag";
import { NationBadge } from "@/components/NationBadge";
import { NationSeatFlag, getNationSeatLabel } from "@/components/NationSeat";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
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
import { copyLink } from "@/utils/copyLink";

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
  const [memberToRemove, setMemberToRemove] = useState<Member | null>(null);

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

  const getDirectChannel = (
    member: Member,
    channels = channelsQuery.data
  ) =>
    channels?.find(channel => {
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
  const isGameMaster =
    !!game.gameMaster && game.gameMaster.userId === userProfile.userId;
  const canTakeOverSeat =
    !game.members.some(m => m.isCurrentUser) && !isGameMaster;
  const playableSeats = variant
    ? variant.nations.filter(n => !n.nonPlayable).length
    : 0;
  const openSeats = isPending
    ? Math.max(0, playableSeats - game.members.length)
    : 0;
  const canAddBots =
    isPending && game.canManage && userProfile.canCreateBotGames;
  const isInactivePower = (member: Member) =>
    !!member.eliminated || !!member.civilDisorder || !!member.kicked;
  const sortedMembers = [...game.members].sort((a, b) => {
    if (game.status === "completed") {
      const winnerOrder =
        Number(winnerIds.includes(b.id)) - Number(winnerIds.includes(a.id));
      if (winnerOrder !== 0) return winnerOrder;
    }

    const inactiveOrder =
      Number(isInactivePower(a)) - Number(isInactivePower(b));
    if (inactiveOrder !== 0) return inactiveOrder;

    return (
      (getSupplyCenterCount(b) ?? 0) - (getSupplyCenterCount(a) ?? 0)
    );
  });

  const canRemove = (member: Member) =>
    game.canManage && !member.isCurrentUser && member.removable;

  const profilePath = (member: Member) =>
    phaseId
      ? `/game/${gameId}/phase/${phaseId}/player/${member.userId}`
      : `/player/${member.userId}`;

  const handleRemove = async () => {
    const member = memberToRemove;
    setMemberToRemove(null);
    if (!member) return;
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
      toast.error("Failed to remove player");
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
      const refreshedChannels = await channelsQuery.refetch();
      const existingChannel = getDirectChannel(
        member,
        refreshedChannels.data
      );
      if (existingChannel) {
        navigate(
          `/game/${gameId}/phase/${phaseId}/chat/channel/${existingChannel.id}`
        );
        return;
      }
      toast.error("Failed to open chat");
    }
  };

  return (
    <>
      <GameStatusAlerts game={game} variant={variant} />
      {isGameMaster && isPending && <NationAssignmentAlert gameId={gameId} />}

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
                  isInactivePower(member) ? "opacity-[0.7]" : ""
                }`}
              >
                {isPending && member.isCurrentUser && variant ? (
                  <NationSeatFlag
                    nations={variant.nations}
                    nation={member.nation}
                    preferenceIds={member.nationPreferenceIds}
                  />
                ) : member.nation && variant ? (
                  flagUrl ? (
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
                  )
                ) : null}

                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    {showNationFocusedLayout ? (
                      <>
                        <span className="font-medium">{member.nation}</span>
                        {member.isCurrentUser && variant && (
                          <NationBadge
                            nations={variant.nations}
                            nation={member.nation}
                          >
                            you
                          </NationBadge>
                        )}
                      </>
                    ) : member.userId ? (
                      <Link
                        to={profilePath(member)}
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
                    {member.kicked && <KickedBadge />}
                    {member.eliminated ? (
                      <Badge variant="secondary">Eliminated</Badge>
                    ) : (
                      member.civilDisorder && <CivilDisorderBadge />
                    )}
                  </div>

                  {member.nation && !isPending && (
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
                            <span>
                              {unitCount} {unitCount === 1 ? "unit" : "units"}
                            </span>
                          ) : (
                            <Skeleton className="h-3 w-10" />
                          )}
                        </span>
                        <span>•</span>
                        <span className="inline-flex items-center gap-1">
                          <Star className="size-3" />
                          {supplyCenterCount !== undefined ? (
                            <span>
                              {supplyCenterCount}{" "}
                              {supplyCenterCount === 1 ? "center" : "centers"}
                            </span>
                          ) : (
                            <Skeleton className="h-3 w-12" />
                          )}
                        </span>
                      </span>
                    </div>
                  )}

                  {member.isCurrentUser && isPending && (
                    <button
                      onClick={() => navigate(`/nation-preference/${gameId}`)}
                      className="flex items-center gap-1 mt-1 text-sm text-muted-foreground hover:text-foreground"
                    >
                      {getNationSeatLabel(
                        member.nation,
                        member.nationPreferenceIds
                      )}
                      <ChevronRight className="size-3.5" />
                    </button>
                  )}

                  {member.replaceable && (
                    <div className="flex flex-wrap gap-2 mt-2">
                      {canTakeOverSeat && (
                        <Button
                          size="sm"
                          onClick={() =>
                            navigate(`/game/${gameId}/replace/${member.id}`)
                          }
                        >
                          <UserPlus />
                          Replace
                        </Button>
                      )}
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() =>
                          copyLink(`/game/${gameId}/replace/${member.id}`)
                        }
                      >
                        <Link2 />
                        Invite replacement
                      </Button>
                    </div>
                  )}
                </div>

                <div className="flex shrink-0 items-center">
                  {showNationFocusedLayout && (
                    <>
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
                                <CommitmentBadge
                                  commitment={member.commitment}
                                />
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
                    </>
                  )}

                  {!showNationFocusedLayout && showChatShortcut && (
                    <Button
                      variant="ghost"
                      size="icon"
                      aria-label={`Message ${member.name}`}
                      disabled={
                        channelsQuery.isLoading ||
                        createChannelMutation.isPending
                      }
                      onClick={() => handleOpenChat(member)}
                    >
                      <MessageCircle className="size-4" />
                    </Button>
                  )}

                  {canRemove(member) && (
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button
                          variant="ghost"
                          size="icon"
                          aria-label={`Options for ${member.name}`}
                        >
                          <MoreVertical />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem
                          onClick={() => setMemberToRemove(member)}
                        >
                          <UserMinus />
                          Remove Player
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  )}
                </div>
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

      <AlertDialog
        open={memberToRemove !== null}
        onOpenChange={open => !open && setMemberToRemove(null)}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>
              Remove {memberToRemove?.nation ?? memberToRemove?.name}
            </AlertDialogTitle>
            <AlertDialogDescription>
              {isPending
                ? `${memberToRemove?.name} is removed from the lobby. They can join again while the game has an open seat.`
                : "Their orders for this phase are discarded and the seat opens for a replacement. They can view the game but cannot rejoin."}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleRemove}>Remove</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

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
