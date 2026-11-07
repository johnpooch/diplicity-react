import React, { Suspense, useState } from "react";
import { Link, useNavigate } from "react-router";
import { useQueryClient } from "@tanstack/react-query";
import {
  Bell,
  BellOff,
  ChevronRight,
  LogOut,
  Megaphone,
  Pencil,
} from "lucide-react";
import { toast } from "sonner";
import { NationFlag, getContrastColor } from "@/components/NationFlag";
import { QueryErrorBoundary } from "@/components/QueryErrorBoundary";
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
import { RowActionButton } from "@/components/ui/role-buttons";
import { Card, CardContent } from "@/components/ui/card";
import { Panel } from "@/components/Panel";
import { useRequiredParams } from "@/hooks";
import { useGameVariant } from "@/hooks/useGameVariant";
import {
  getGamesChannelPreviewsListQueryKey,
  getGamesChannelsRetrieveQueryKey,
  useGameRetrieveSuspense,
  useGamesChannelsLeaveCreate,
  useGamesChannelsMutePartialUpdate,
  useGamesChannelsRetrieveSuspense,
} from "@/api/generated/endpoints";
import { GameDetailAppBar } from "./AppBar";
import { ChannelAvatar } from "./ChannelAvatar";
import {
  getChannelDisplayName,
  getChannelMemberNations,
} from "./channelUtils";

const ChannelOptionsScreen: React.FC = () => {
  const { gameId, phaseId, channelId } = useRequiredParams<{
    gameId: string;
    phaseId: string;
    channelId: string;
  }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { data: game } = useGameRetrieveSuspense(gameId);
  const { data: channel } = useGamesChannelsRetrieveSuspense(
    gameId,
    Number(channelId)
  );
  const variant = useGameVariant(game);
  const muteMutation = useGamesChannelsMutePartialUpdate();
  const leaveMutation = useGamesChannelsLeaveCreate();
  const [showLeaveConfirmation, setShowLeaveConfirmation] = useState(false);

  const currentMember = game.members.find(member => member.isCurrentUser);
  const currentNationName = currentMember?.nation ?? undefined;
  const displayName = getChannelDisplayName(channel, currentNationName);
  const channelMembers = getChannelMemberNations(
    channel,
    game.members,
    variant?.nations ?? []
  );
  const memberCount = channelMembers.length;

  const handleMute = async () => {
    try {
      await muteMutation.mutateAsync({
        gameId,
        channelId: channel.id,
        data: { muteDuration: "indefinite" },
      });
      await Promise.all([
        queryClient.invalidateQueries({
          queryKey: getGamesChannelsRetrieveQueryKey(gameId, channel.id),
        }),
        queryClient.invalidateQueries({
          queryKey: getGamesChannelPreviewsListQueryKey(gameId),
        }),
      ]);
    } catch {
      toast.error("There was an error muting this channel");
    }
  };

  const handleUnmute = async () => {
    try {
      await muteMutation.mutateAsync({
        gameId,
        channelId: channel.id,
        data: { muteDuration: null },
      });
      await Promise.all([
        queryClient.invalidateQueries({
          queryKey: getGamesChannelsRetrieveQueryKey(gameId, channel.id),
        }),
        queryClient.invalidateQueries({
          queryKey: getGamesChannelPreviewsListQueryKey(gameId),
        }),
      ]);
    } catch {
      toast.error("There was an error unmuting this channel");
    }
  };

  const handleLeave = async () => {
    setShowLeaveConfirmation(false);
    try {
      await leaveMutation.mutateAsync({ gameId, channelId: channel.id });
      navigate(`/game/${gameId}/phase/${phaseId}/chat`);
      queryClient.removeQueries({
        queryKey: getGamesChannelsRetrieveQueryKey(gameId, channel.id),
      });
      queryClient.invalidateQueries({
        queryKey: getGamesChannelPreviewsListQueryKey(gameId),
      });
    } catch {
      toast.error("There was an error leaving this channel");
    }
  };

  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <GameDetailAppBar
        title="Chat options"
        variant="secondary"
        onNavigateBack={() =>
          navigate(`/game/${gameId}/phase/${phaseId}/chat/channel/${channelId}`)
        }
      />
      <Panel>
        <Panel.Content className="px-3 py-6">
          <div className="mx-auto flex w-full max-w-xl flex-col items-center gap-6">
            <div className="flex flex-col items-center gap-3 text-center">
              {channel.private ? (
                <ChannelAvatar
                  size={96}
                  nations={channelMembers}
                />
              ) : (
                <div className="flex size-24 items-center justify-center rounded-full bg-muted ring-4 ring-border">
                  <Megaphone className="size-10 text-muted-foreground" />
                </div>
              )}
              <div>
                <h2 className="text-2xl font-semibold">{displayName}</h2>
              </div>
            </div>
            {(channel.canRename || channel.canMute || channel.canLeave) && (
              <Card className="w-full overflow-hidden py-0">
                <CardContent className="flex flex-col divide-y p-0">
                  {channel.canRename && (
                    <RowActionButton asChild>
                      <Link
                        to={`/game/${gameId}/phase/${phaseId}/chat/channel/${channelId}/rename`}
                      >
                        <Pencil />
                        <span className="flex-1">Rename channel</span>
                        <ChevronRight className="text-muted-foreground" />
                      </Link>
                    </RowActionButton>
                  )}
                  {channel.canMute &&
                    (channel.muted ? (
                      <RowActionButton
                        onClick={handleUnmute}
                        disabled={muteMutation.isPending}
                      >
                        <Bell />
                        <span className="flex-1">
                          Unmute notifications
                        </span>
                      </RowActionButton>
                    ) : (
                      <RowActionButton
                        onClick={handleMute}
                        disabled={muteMutation.isPending}
                      >
                        <BellOff />
                        <span className="flex-1">
                          Mute notifications
                        </span>
                      </RowActionButton>
                    ))}
                  {channel.canLeave && (
                    <RowActionButton
                      onClick={() => setShowLeaveConfirmation(true)}
                      disabled={leaveMutation.isPending}
                    >
                      <LogOut />
                      <span className="flex-1">Leave channel</span>
                    </RowActionButton>
                  )}
                </CardContent>
              </Card>
            )}
            <section
              className="w-full space-y-2"
              aria-labelledby="channel-members-heading"
            >
              <h3
                id="channel-members-heading"
                className="px-1 text-sm font-medium text-muted-foreground"
              >
                {memberCount} {memberCount === 1 ? "member" : "members"}
              </h3>
              <Card className="w-full overflow-hidden py-0">
                <CardContent
                  className="flex flex-col divide-y p-0"
                  role="list"
                  aria-labelledby="channel-members-heading"
                >
                  {channelMembers.map(member => (
                    <div
                      key={member.name}
                      className="flex items-center gap-3 px-4 py-3"
                      role="listitem"
                    >
                      <div className="relative size-12 shrink-0">
                        <div
                          className="size-12 overflow-hidden rounded-full"
                          style={{
                            boxShadow: `0 0 0 3px ${member.color}`,
                          }}
                        >
                          <NationFlag
                            flagUrl={member.flagUrl}
                            color={member.color}
                            alt={member.name}
                            className="size-12"
                          />
                        </div>
                        {member.playerUserId !== null && (
                          <span className="absolute -bottom-0.5 -right-0.5">
                            <Avatar className="size-5 ring-2 ring-background">
                              <AvatarImage
                                src={member.playerPicture ?? undefined}
                              />
                              <AvatarFallback
                                className="text-[8px] leading-none"
                                style={{
                                  backgroundColor: member.color,
                                  color: getContrastColor(member.color),
                                }}
                              >
                                {member.playerName?.[0]?.toUpperCase() ?? "?"}
                              </AvatarFallback>
                            </Avatar>
                          </span>
                        )}
                      </div>
                      <div className="min-w-0 flex-1">
                        <p className="truncate font-medium">{member.name}</p>
                        {member.playerName && (
                          <p className="mt-0.5 truncate text-sm text-muted-foreground">
                            {member.playerName}
                          </p>
                        )}
                      </div>
                    </div>
                  ))}
                </CardContent>
              </Card>
            </section>
          </div>
        </Panel.Content>
      </Panel>
      <AlertDialog
        open={showLeaveConfirmation}
        onOpenChange={setShowLeaveConfirmation}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Leave channel</AlertDialogTitle>
            <AlertDialogDescription>
              You will no longer see this conversation or receive its
              notifications. Once you leave, you cannot rejoin this channel.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleLeave}>Leave</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
};

const ChannelOptionsScreenSuspense: React.FC = () => (
  <QueryErrorBoundary>
    <Suspense fallback={<div />}>
      <ChannelOptionsScreen />
    </Suspense>
  </QueryErrorBoundary>
);

export { ChannelOptionsScreenSuspense as ChannelOptionsScreen };
