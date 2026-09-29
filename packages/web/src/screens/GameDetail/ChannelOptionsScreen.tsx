import React, { Suspense } from "react";
import { Link, useNavigate } from "react-router";
import { useQueryClient } from "@tanstack/react-query";
import { Bell, BellOff, ChevronRight, Megaphone, Pencil } from "lucide-react";
import { toast } from "sonner";
import { QueryErrorBoundary } from "@/components/QueryErrorBoundary";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { Panel } from "@/components/Panel";
import { useRequiredParams } from "@/hooks";
import { useGameVariant } from "@/hooks/useGameVariant";
import {
  getGamesChannelsListQueryKey,
  useGameRetrieveSuspense,
  useGamesChannelsListSuspense,
  useGamesChannelsMutePartialUpdate,
  useUserRetrieveSuspense,
} from "@/api/generated/endpoints";
import { GameDetailAppBar } from "./AppBar";
import { ChannelAvatar } from "./ChannelAvatar";
import {
  getChannelDisplayName,
  getChannelMemberFlagUrls,
  getChannelMemberLabels,
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
  const { data: userProfile } = useUserRetrieveSuspense();
  const { data: channels } = useGamesChannelsListSuspense(gameId);
  const variant = useGameVariant(game);
  const muteMutation = useGamesChannelsMutePartialUpdate();
  const channel = channels.find(item => item.id === Number(channelId));
  if (!channel) throw new Error("Channel not found");

  const currentMember = game.members.find(member => member.isCurrentUser);
  const isGameMaster = game.gameMaster?.userId === userProfile.userId;
  const currentNationName = currentMember?.nation ?? undefined;
  const displayName = getChannelDisplayName(channel, currentNationName);
  const memberLabels = getChannelMemberLabels(channel, game.members);
  if (!channel.private && game.gameMaster) {
    memberLabels.push(`Game Master — ${game.gameMaster.name}`);
  }
  const memberCount = memberLabels.length;
  const noPressActive =
    game.pressType === "no_press" &&
    game.status !== "completed" &&
    game.status !== "abandoned";
  const canRename =
    channel.private &&
    !!currentMember &&
    !currentMember.kicked &&
    !game.sandbox &&
    !noPressActive;
  const canMute = !!currentMember || isGameMaster;

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
      toast.success(`Successfully muted ${displayName}`);
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
      toast.success(`Successfully unmuted ${displayName}`);
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
                  nations={getChannelMemberFlagUrls(
                    channel,
                    game.members,
                    variant?.nations ?? []
                  )}
                />
              ) : (
                <div className="flex size-24 items-center justify-center rounded-full bg-muted ring-4 ring-border">
                  <Megaphone className="size-10 text-muted-foreground" />
                </div>
              )}
              <div>
                <h2 className="text-2xl font-semibold">{displayName}</h2>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <button
                      type="button"
                      className="cursor-pointer text-sm text-muted-foreground underline-offset-4 hover:underline focus-visible:rounded-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                    >
                      {memberCount} {memberCount === 1 ? "member" : "members"}
                    </button>
                  </TooltipTrigger>
                  <TooltipContent side="bottom" className="max-w-xs">
                    <ul className="space-y-1">
                      {memberLabels.map((label, index) => (
                        <li key={`${label}-${index}`}>{label}</li>
                      ))}
                    </ul>
                  </TooltipContent>
                </Tooltip>
              </div>
            </div>
            <Card className="w-full overflow-hidden py-0">
              <CardContent className="flex flex-col divide-y p-0">
                {canRename && (
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
                {canMute &&
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
