import React, { Suspense } from "react";
import { Link, useNavigate } from "react-router";
import { useQueryClient } from "@tanstack/react-query";
import { Bell, BellOff, ChevronRight, Megaphone, Pencil } from "lucide-react";
import { toast } from "sonner";
import { NationFlag, getContrastColor } from "@/components/NationFlag";
import { QueryErrorBoundary } from "@/components/QueryErrorBoundary";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Panel } from "@/components/Panel";
import { useRequiredParams } from "@/hooks";
import { useGameVariant } from "@/hooks/useGameVariant";
import {
  getGamesChannelsListQueryKey,
  useGameRetrieveSuspense,
  useGamesChannelsListSuspense,
  useGamesChannelsMutePartialUpdate,
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
  const { data: channels } = useGamesChannelsListSuspense(gameId);
  const variant = useGameVariant(game);
  const muteMutation = useGamesChannelsMutePartialUpdate();
  const channel = channels.find(item => item.id === Number(channelId));
  if (!channel) throw new Error("Channel not found");

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
      await queryClient.invalidateQueries({
        queryKey: getGamesChannelsListQueryKey(gameId),
      });
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
      await queryClient.invalidateQueries({
        queryKey: getGamesChannelsListQueryKey(gameId),
      });
    } catch {
      toast.error("There was an error unmuting this channel");
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
            {(channel.canRename || channel.canMute) && (
              <Card className="w-full overflow-hidden py-0">
                <CardContent className="flex flex-col divide-y p-0">
                  {channel.canRename && (
                    <Button
                      variant="ghost"
                      className="h-auto w-full cursor-pointer justify-start rounded-none px-4 py-4"
                      asChild
                    >
                      <Link
                        to={`/game/${gameId}/phase/${phaseId}/chat/channel/${channelId}/rename`}
                      >
                        <Pencil />
                        <span className="flex-1 text-left">Rename channel</span>
                        <ChevronRight className="text-muted-foreground" />
                      </Link>
                    </Button>
                  )}
                  {channel.canMute &&
                    (channel.muted ? (
                      <Button
                        variant="ghost"
                        className="h-auto w-full cursor-pointer justify-start rounded-none px-4 py-4"
                        onClick={handleUnmute}
                        disabled={muteMutation.isPending}
                      >
                        <Bell />
                        <span className="flex-1 text-left">
                          Unmute notifications
                        </span>
                      </Button>
                    ) : (
                      <Button
                        variant="ghost"
                        className="h-auto w-full cursor-pointer justify-start rounded-none px-4 py-4"
                        onClick={handleMute}
                        disabled={muteMutation.isPending}
                      >
                        <BellOff />
                        <span className="flex-1 text-left">
                          Mute notifications
                        </span>
                      </Button>
                    ))}
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
