import React, { Suspense } from "react";
import { Link, Navigate, useSearchParams } from "react-router";
import {
  MessageSquare,
  MessageSquareOff,
  MessageSquarePlus,
  Megaphone,
} from "lucide-react";
import { useRequiredParams } from "@/hooks";

import { QueryErrorBoundary } from "@/components/QueryErrorBoundary";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Notice } from "@/components/Notice";
import { GameDetailAppBar } from "./AppBar";
import { Panel } from "../../components/Panel";
import {
  ChannelMessage,
  useGameRetrieveSuspense,
  useGamesChannelsListSuspense,
} from "@/api/generated/endpoints";
import { useGameVariant } from "@/hooks/useGameVariant";
import {
  getChannelDisplayName,
  getChannelFlagUrls,
  getMessageSenderLabel,
} from "./channelUtils";
import { ChannelAvatar } from "./ChannelAvatar";

const getLatestMessagePreview = (
  messages: readonly ChannelMessage[]
): string => {
  if (messages.length === 0) return "No messages";
  const latestMessage = messages[messages.length - 1];
  const senderLabel = latestMessage.sender.isCurrentUser
    ? "You"
    : getMessageSenderLabel(latestMessage.sender);
  return `${senderLabel}: ${latestMessage.body}`;
};

const ChannelListScreen: React.FC = () => {
  const { gameId, phaseId } = useRequiredParams<{
    gameId: string;
    phaseId: string;
  }>();
  const { data: game } = useGameRetrieveSuspense(gameId);
  const { data: channels } = useGamesChannelsListSuspense(gameId);
  const variant = useGameVariant(game);

  const currentMember = game.members.find(m => m.isCurrentUser);
  const currentNationName = currentMember?.nation ?? undefined;
  const variantNations = variant?.nations ?? [];
  const isSandboxGame = game.sandbox;
  const isNoPressActiveGame =
    game.pressType === "no_press" &&
    game.status !== "completed" &&
    game.status !== "abandoned";
  const canCreateChannel = !!currentMember && !isSandboxGame && !isNoPressActiveGame;

  return (
    <div className="flex flex-col flex-1 min-h-0">
      <GameDetailAppBar
        title="Chats"
        rightButton={
          canCreateChannel ? (
            <Button variant="outline" size="icon" aria-label="Create channel" asChild>
              <Link to={`/game/${gameId}/phase/${phaseId}/chat/channel/create`}>
                <MessageSquarePlus />
              </Link>
            </Button>
          ) : undefined
        }
      />
      <div className="flex-1 overflow-y-auto">
        <Panel>
          <Panel.Content className="flex flex-col gap-4 px-3 py-4">
            {isSandboxGame ? (
              <Notice
                icon={MessageSquare}
                title="Chat is not available in sandbox games."
                className="h-full"
              />
            ) : isNoPressActiveGame ? (
              <Notice
                icon={MessageSquareOff}
                title="Messaging is disabled in No Press games."
                className="h-full"
              />
            ) : channels.length === 0 ? (
              <Notice
                icon={MessageSquare}
                title="No channels created"
                className="h-full"
              />
            ) : (
              <Card className="shrink-0 overflow-hidden py-0">
                <CardContent className="flex flex-col divide-y p-0">
                  {channels.map(channel => (
                    <Link
                      key={channel.id}
                      to={`/game/${gameId}/phase/${phaseId}/chat/channel/${channel.id}`}
                      className="flex items-center gap-3 p-3 transition-colors hover:bg-accent/50"
                    >
                      {channel.private ? (
                        <ChannelAvatar
                          size={48}
                          nations={getChannelFlagUrls(
                            channel,
                            game.members,
                            currentNationName,
                            variantNations
                          )}
                        />
                      ) : (
                        <div
                          className="flex size-12 shrink-0 items-center justify-center rounded-full ring-3 ring-border bg-muted"
                          aria-label="Public channel"
                        >
                          <Megaphone className="size-5 text-muted-foreground" />
                        </div>
                      )}
                      <div className="flex min-w-0 flex-1 flex-col gap-0.5">
                        <span className="truncate font-semibold leading-tight">
                          {getChannelDisplayName(channel, currentNationName)}
                        </span>
                        <p className="truncate text-sm text-muted-foreground">
                          {getLatestMessagePreview(channel.messages)}
                        </p>
                      </div>
                      {channel.unreadMessageCount > 0 && (
                        <Badge className="h-5 min-w-5 shrink-0 justify-center rounded-full px-1 leading-none">
                          {channel.unreadMessageCount}
                        </Badge>
                      )}
                    </Link>
                  ))}
                </CardContent>
              </Card>
            )}
            {canCreateChannel && (
              <Button className="w-full" size="lg" asChild>
                <Link to={`/game/${gameId}/phase/${phaseId}/chat/channel/create`}>
                  <MessageSquarePlus />
                  Create Channel
                </Link>
              </Button>
            )}
          </Panel.Content>
        </Panel>
      </div>
    </div>
  );
};

const ChannelListScreenSuspense: React.FC = () => {
  const { gameId, phaseId } = useRequiredParams<{ gameId: string; phaseId: string }>();
  const [searchParams] = useSearchParams();
  const channelId = searchParams.get("channelId");

  if (channelId) {
    return <Navigate to={`/game/${gameId}/phase/${phaseId}/chat/channel/${channelId}`} replace />;
  }

  return (
    <QueryErrorBoundary>
      <Suspense fallback={<div></div>}>
        <ChannelListScreen />
      </Suspense>
    </QueryErrorBoundary>
  );
};

export { ChannelListScreenSuspense as ChannelListScreen };
