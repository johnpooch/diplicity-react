import React, { Suspense, useRef, useEffect, useState, useMemo } from "react";
import { useNavigate, useSearchParams } from "react-router";
import { useQueryClient } from "@tanstack/react-query";
import { SendHorizontal, MessageCircle, MessageSquareOff, Map } from "lucide-react";
import { useDraft, useRequiredParams } from "@/hooks";
import { useIsDesktopWeb } from "@/hooks/use-platform";
import { toast } from "sonner";

import { QueryErrorBoundary } from "@/components/QueryErrorBoundary";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import {
  Message,
  MessageContent,
  MessageTimestamp,
} from "@/components/ui/message";
import { Notice } from "@/components/Notice";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { NationFlag, findNationFlagUrl } from "@/components/NationFlag";
import { cn } from "@/lib/utils";
import { GameDetailAppBar } from "./AppBar";
import { getChannelDisplayName, getChannelSubtitle, getChannelFlagUrls, brightnessByColor, toHex6 } from "./channelUtils";
import { ChannelAvatar } from "./ChannelAvatar";
import { ChannelRenameDialog } from "./ChannelRenameDialog";
import { Panel } from "@/components/Panel";
import {
  useGameRetrieveSuspense,
  useGamesChannelsListSuspense,
  useGamesChannelsMessagesCreateCreate,
  useGamesChannelsMarkReadCreate,
  getGamesChannelsListQueryKey,
  getGameRetrieveQueryKey,
  ChannelMessage as ChannelMessageType,
} from "@/api/generated/endpoints";
import { useGameVariant } from "@/hooks/useGameVariant";

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
    const nationName = msg.sender.nation?.name ?? msg.sender.name;
    const previousNationName = index > 0
      ? messages[index - 1].sender.nation?.name ?? messages[index - 1].sender.name
      : null;
    const showAvatar = index === 0 || previousNationName !== nationName;

    return {
      id: msg.id,
      body: msg.body,
      createdAt: msg.createdAt,
      sender: {
        nationName,
        nationColor: msg.sender.nation?.color ?? "#808080",
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
  const isDesktopWeb = useIsDesktopWeb();
  const [message, setMessage] = useDraft(gameId, channelId);
  const [isSubtitleOpen, setIsSubtitleOpen] = useState(false);
  const [, setSearchParams] = useSearchParams();

  const { data: game } = useGameRetrieveSuspense(gameId);
  const { data: channels } = useGamesChannelsListSuspense(gameId, {
    query: {
      refetchInterval: 5000,
    },
  });
  const variant = useGameVariant(game);
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
  const channelDisplayName = getChannelDisplayName(channel, currentNationName);
  const channelFlagUrls = getChannelFlagUrls(
    channel,
    game.members,
    currentNationName,
    variant?.nations ?? []
  );
  const channelSubtitle = getChannelSubtitle(channel, game.members, currentNationName);
  const channelTitle = (
    <div className="flex items-center justify-start gap-2">
      <ChannelAvatar nations={channelFlagUrls} />
      <div className="min-w-0 flex-1 text-left">
        <p className="truncate text-lg font-semibold leading-tight">{channelDisplayName}</p>
        {channelSubtitle && (
          <Tooltip open={isSubtitleOpen} onOpenChange={setIsSubtitleOpen}>
            <TooltipTrigger
              className="block w-full truncate text-left text-xs leading-tight text-muted-foreground"
              onClick={() => setIsSubtitleOpen(true)}
            >
              {channelSubtitle}
            </TooltipTrigger>
            <TooltipContent>{channelSubtitle}</TooltipContent>
          </Tooltip>
        )}
      </div>
    </div>
  );
  const headerButtons = (
    <>
      {channel.private && currentMember && (
        <ChannelRenameDialog gameId={gameId} channel={channel} />
      )}
      <Button
        variant="outline"
        size="icon-sm"
        className="rounded-full md:hidden"
        aria-label="Map preview"
        onClick={() => navigate(`/game/${gameId}/phase/${phaseId}`)}
      >
        <Map />
      </Button>
    </>
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
    if (!isDesktopWeb) return;
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
          rightButton={headerButtons}
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
        rightButton={headerButtons}
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
                  className="flex-1 min-h-0 overflow-y-auto flex flex-col gap-3 px-3 py-4"
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
                          <div className="size-8 shrink-0 overflow-hidden rounded-full border">
                            <NationFlag
                              flagUrl={
                                variant
                                  ? findNationFlagUrl(variant.nations, item.sender.nationName)
                                  : null
                              }
                              alt={item.sender.nationName}
                              className="size-8"
                              color={item.sender.nationColor}
                            />
                          </div>
                        ) : (
                          <div className="size-8 shrink-0" />
                        )}
                        <div className="max-w-[80%]">
                          <MessageContent
                            className={`py-1.5 px-2 ${item.isCurrentUser ? "rounded-tr-none" : "rounded-tl-none"}`}
                            style={{
                              backgroundColor: toHex6(item.sender.nationColor) + BUBBLE_ALPHA_HEX,
                              border: brightnessByColor(item.sender.nationColor) > 128
                                ? `1px solid ${item.sender.nationColor}`
                                : undefined,
                            }}
                          >
                            {item.showAvatar && (
                              <p
                                className="mb-0.5 text-xs font-semibold"
                                style={{ color: item.sender.nationColor }}
                              >
                                {item.isCurrentUser ? "You" : item.sender.nationName}
                              </p>
                            )}
                            {item.body}
                          </MessageContent>
                          <MessageTimestamp
                            className={cn("mt-0.5", !item.isCurrentUser && "text-left")}
                          >
                            {item.formattedTime}
                          </MessageTimestamp>
                        </div>
                      </Message>
                    </React.Fragment>
                  ))}
                </div>
              )}
            </div>
          </Panel.Content>
          {currentMember && (
            <Panel.Footer className="px-2 py-2 md:px-3">
              <div className="flex gap-2 w-full">
                <Textarea
                  placeholder="Type a message"
                  value={message}
                  rows={1}
                  maxLength={500}
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
                  <SendHorizontal />
                </Button>
              </div>
            </Panel.Footer>
          )}
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
