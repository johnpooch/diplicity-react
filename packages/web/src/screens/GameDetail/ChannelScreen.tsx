import React, { Suspense, useRef, useEffect, useState, useMemo } from "react";
import { useNavigate, useSearchParams } from "react-router";
import { useQueryClient } from "@tanstack/react-query";
import { Send, MessageCircle, MessageSquareOff } from "lucide-react";
import { useDraft, useRequiredParams } from "@/hooks";
import { useIsMobile } from "@/hooks/use-mobile";
import { toast } from "sonner";

import { QueryErrorBoundary } from "@/components/QueryErrorBoundary";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Separator } from "@/components/ui/separator";
import {
  Message,
  MessageContent,
  MessageTimestamp,
} from "@/components/ui/message";
import { Notice } from "@/components/Notice";
import { NationFlag, findNationFlagUrl } from "@/components/NationFlag";
import { GameDetailAppBar } from "./AppBar";
import { getChannelDisplayName, getChannelFlagUrls, brightnessByColor, toHex6 } from "./channelUtils";
import { ChannelAvatar } from "./ChannelAvatar";
import { Panel } from "@/components/Panel";
import {
  useGameRetrieveSuspense,
  useGamesChannelsListSuspense,
  useVariantsListSuspense,
  useGamesChannelsMessagesCreateCreate,
  useGamesChannelsMarkReadCreate,
  getGamesChannelsListQueryKey,
  getGameRetrieveQueryKey,
  ChannelMessage as ChannelMessageType,
} from "@/api/generated/endpoints";

type MessageDisplayItem = {
  id: number;
  body: string;
  createdAt: string;
  sender: {
    nationName: string;
    nationColor: string;
    picture: string | null;
  };
  isCurrentUser: boolean;
  showAvatar: boolean;
  formattedTime: string;
};

const formatMessageTime = (createdAt: string): string => {
  const date = new Date(createdAt);
  const today = new Date();
  const isToday =
    date.getFullYear() === today.getFullYear() &&
    date.getMonth() === today.getMonth() &&
    date.getDate() === today.getDate();
  const time = date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  if (isToday) return time;
  return `${date.toLocaleDateString([], { month: "short", day: "numeric" })} ${time}`;
};

const buildMessageItems = (
  messages: readonly ChannelMessageType[]
): MessageDisplayItem[] => {
  return messages.map((msg, index) => {
    const showAvatar =
      index === 0 ||
      messages[index - 1].sender.nation.name !== msg.sender.nation.name;

    return {
      id: msg.id,
      body: msg.body,
      createdAt: msg.createdAt,
      sender: {
        nationName: msg.sender.nation.name,
        nationColor: msg.sender.nation.color,
        picture: msg.sender.picture,
      },
      isCurrentUser: msg.sender.isCurrentUser,
      showAvatar,
      formattedTime: formatMessageTime(msg.createdAt),
    };
  });
};

const BUBBLE_ALPHA_HEX = "26"; // 15% opacity (0x26/0xFF)

const NewMessagesDivider: React.FC = () => (
  <div className="flex items-center gap-2 my-1">
    <div className="flex-1 h-px bg-border" />
    <span className="text-xs text-muted-foreground font-medium">New messages</span>
    <div className="flex-1 h-px bg-border" />
  </div>
);

const ChannelScreen: React.FC = () => {
  const { gameId, phaseId, channelId } = useRequiredParams<{
    gameId: string;
    phaseId: string;
    channelId: string;
  }>();

  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const isMobile = useIsMobile();
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
    if (isMobile) return;
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
    () => buildMessageItems(channel.messages),
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
              {channel.messages.length === 0 ? (
                <Notice
                  icon={MessageCircle}
                  title="No messages yet"
                  message="Start the conversation by sending a message"
                  className="h-full"
                />
              ) : (
                <div
                  ref={messagesContainerRef}
                  className="flex-1 min-h-0 overflow-y-auto flex flex-col gap-2 p-2"
                >
                  {messageItems.map((item, index) => (
                    <React.Fragment key={item.id}>
                      {firstUnreadIndex !== null && index === firstUnreadIndex && (
                        <NewMessagesDivider />
                      )}
                      <Message
                        className={
                          item.isCurrentUser ? "flex-row-reverse" : undefined
                        }
                      >
                        {item.showAvatar ? (
                          <div className="w-8 flex-shrink-0 flex justify-center">
                            <NationFlag
                              flagUrl={
                                variant
                                  ? findNationFlagUrl(variant.nations, item.sender.nationName)
                                  : null
                              }
                              alt={item.sender.nationName}
                              size="lg"
                              color={item.sender.nationColor}
                            />
                          </div>
                        ) : (
                          <div className="w-8 flex-shrink-0" />
                        )}
                        <MessageContent
                          className={`py-1.5 px-2 ${item.isCurrentUser ? "rounded-tr-none" : "rounded-tl-none"}`}
                          style={{
                            backgroundColor: toHex6(item.sender.nationColor) + BUBBLE_ALPHA_HEX,
                            border: brightnessByColor(item.sender.nationColor) > 128
                              ? `1px solid ${item.sender.nationColor}`
                              : undefined,
                          }}
                        >
                          {item.body}
                          {item.showAvatar ? (
                            <div className="flex items-center justify-between gap-2 mt-0.5">
                              <span
                                className="text-xs font-medium"
                                style={{ color: item.sender.nationColor }}
                              >
                                {item.sender.nationName}
                              </span>
                              <span className="text-xs text-muted-foreground">
                                {item.formattedTime}
                              </span>
                            </div>
                          ) : (
                            <MessageTimestamp className="mt-0.5">
                              {item.formattedTime}
                            </MessageTimestamp>
                          )}
                        </MessageContent>
                      </Message>
                    </React.Fragment>
                  ))}
                </div>
              )}
            </div>
          </Panel.Content>
          <Separator />
          <Panel.Footer>
            <div className="flex gap-2 w-full">
              <Textarea
                placeholder="Type a message"
                value={message}
                rows={1}
                enterKeyHint="enter"
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
