import React, { Suspense, useRef, useEffect, useState, useMemo } from "react";
import { useNavigate, useSearchParams } from "react-router";
import { useQueryClient } from "@tanstack/react-query";
import { Send, MessageSquareOff } from "lucide-react";
import { useDraft, useRequiredParams } from "@/hooks";
import { toast } from "sonner";

import { QueryErrorBoundary } from "@/components/QueryErrorBoundary";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Separator } from "@/components/ui/separator";
import { Notice } from "@/components/Notice";
import { GameDetailAppBar } from "./AppBar";
import { getChannelDisplayName, getChannelFlagUrls } from "./channelUtils";
import { ChannelAvatar } from "./ChannelAvatar";
import { Panel } from "@/components/Panel";
import { buildMessageDisplayItems, ChannelMessageList } from "./ChannelMessageList";
import {
  useGameRetrieveSuspense,
  useGamesChannelsListSuspense,
  useVariantsListSuspense,
  useGamesChannelsMessagesCreateCreate,
  useGamesChannelsMarkReadCreate,
  getGamesChannelsListQueryKey,
  getGameRetrieveQueryKey,
} from "@/api/generated/endpoints";


const ChannelScreen: React.FC = () => {
  const { gameId, phaseId, channelId } = useRequiredParams<{
    gameId: string;
    phaseId: string;
    channelId: string;
  }>();

  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [message, setMessage] = useDraft(gameId, channelId);
  const [, setSearchParams] = useSearchParams();

  const { data: game } = useGameRetrieveSuspense(gameId);
  const { data: channels } = useGamesChannelsListSuspense(gameId);
  const { data: variants } = useVariantsListSuspense();
  const createMessageMutation = useGamesChannelsMessagesCreateCreate();
  const markReadMutation = useGamesChannelsMarkReadCreate();

  const messagesContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setSearchParams(prev => {
      const next = new URLSearchParams(prev);
      next.set("channelId", channelId);
      return next;
    }, { replace: true });
  }, [channelId, setSearchParams]);

  const channel = channels.find(c => c.id === parseInt(channelId));
  if (!channel) throw new Error("Channel not found");

  const [firstUnreadIndex] = useState<number | null>(() => {
    const count = channel.unreadMessageCount;
    if (count <= 0) return null;
    const idx = channel.messages.length - count;
    return idx > 0 ? idx : null;
  });

  const currentMember = game.members.find(m => m.isCurrentUser);
  const currentNationName = currentMember?.nation ?? undefined;
  const variant = variants.find(v => v.id === game.variantId);
  const channelDisplayName = getChannelDisplayName(channel, currentNationName);
  const channelFlagUrls = getChannelFlagUrls(
    channel,
    game.members,
    currentNationName,
    variant?.nations ?? []
  );
  const channelTitle = (
    <div className="flex items-center justify-start gap-2">
      <ChannelAvatar nations={channelFlagUrls} />
      <span className="text-lg font-semibold truncate text-left">{channelDisplayName}</span>
    </div>
  );

  useEffect(() => {
    if (!currentMember) return;
    markReadMutation.mutateAsync({
      gameId,
      channelId: parseInt(channelId),
    }).then(() => {
      queryClient.invalidateQueries({
        queryKey: getGamesChannelsListQueryKey(gameId),
      });
      queryClient.invalidateQueries({
        queryKey: getGameRetrieveQueryKey(gameId),
      });
    }).catch(() => {
      // Fire-and-forget: silently ignore mark-read failures
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps -- mutation object excluded per project convention (not referentially stable); fire once on mount
  }, [gameId, channelId]);

  useEffect(() => {
    if (messagesContainerRef.current) {
      messagesContainerRef.current.scrollTop =
        messagesContainerRef.current.scrollHeight;
    }
  }, [channel.messages]);

  const handleSubmit = async () => {
    if (!message.trim()) return;

    try {
      await createMessageMutation.mutateAsync({
        gameId,
        channelId: parseInt(channelId),
        data: { body: message },
      });
      setMessage("");
      queryClient.invalidateQueries({
        queryKey: getGamesChannelsListQueryKey(gameId),
      });
    } catch {
      toast.error("Failed to send message");
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const isNoPressActiveGame =
    game.pressType === "no_press" &&
    game.status !== "completed" &&
    game.status !== "abandoned";

  const messageItems = useMemo(
    () => buildMessageDisplayItems(channel.messages),
    [channel.messages]
  );

  if (isNoPressActiveGame) {
    return (
      <div className="flex flex-col flex-1 min-h-0">
        <GameDetailAppBar
          title={channelTitle}
          onNavigateBack={() =>
            navigate(`/game/${gameId}/phase/${phaseId}/chat`)
          }
          variant="secondary"
        />
        <div className="flex-1 overflow-hidden">
          <Panel>
            <Panel.Content>
              <Notice
                icon={MessageSquareOff}
                title="Messaging is disabled in No Press games."
                className="h-full"
              />
            </Panel.Content>
          </Panel>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col flex-1 min-h-0">
      <GameDetailAppBar
        title={channelTitle}
        onNavigateBack={() => navigate(`/game/${gameId}/phase/${phaseId}/chat`)}
        variant="secondary"
      />
      <div className="flex-1 overflow-hidden">
        <Panel>
          <Panel.Content>
            <div className="h-full flex flex-col">
              <ChannelMessageList
                messageItems={messageItems}
                variantNations={variant?.nations ?? []}
                firstUnreadIndex={firstUnreadIndex}
                scrollContainerRef={messagesContainerRef}
                emptyMessage="Start the conversation by sending a message"
              />
            </div>
          </Panel.Content>
          <Separator />
          <Panel.Footer>
            <div className="flex gap-2 w-full">
              <Textarea
                placeholder="Type a message"
                value={message}
                rows={1}
                onChange={e => setMessage(e.target.value)}
                onKeyDown={handleKeyDown}
                disabled={createMessageMutation.isPending}
                className="flex-1 min-h-0 max-h-32 resize-none py-2"
              />
              <Button
                onClick={handleSubmit}
                disabled={!message.trim() || createMessageMutation.isPending}
                size="icon"
              >
                <Send className="size-4" />
              </Button>
            </div>
          </Panel.Footer>
        </Panel>
      </div>
    </div>
  );
};

const ChannelScreenSuspense: React.FC = () => (
  <QueryErrorBoundary>
    <Suspense fallback={<div></div>}>
      <ChannelScreen />
    </Suspense>
  </QueryErrorBoundary>
);

export { ChannelScreenSuspense as ChannelScreen };
