import React, { Suspense, useRef, useEffect, useState, useMemo } from "react";
import { Link, useNavigate, useSearchParams } from "react-router";
import { useQueryClient } from "@tanstack/react-query";
import { SendHorizontal, MessageCircle, MessageSquareOff, Pencil } from "lucide-react";
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
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { NationFlag, findNationFlagUrl } from "@/components/NationFlag";
import { cn } from "@/lib/utils";
import { GameDetailAppBar } from "./AppBar";
import {
  getChannelDisplayName,
  getChannelSubtitle,
  isGroupChannel,
  getMessageSenderLabel,
  brightnessByColor,
  toHex6,
  NEUTRAL_SENDER_COLOR,
} from "./channelUtils";
import { Panel } from "@/components/Panel";
import {
  useGameRetrieveSuspense,
  useUserRetrieveSuspense,
  useGamesChannelsListSuspense,
  useGamesChannelsMessagesCreateCreate,
  useGamesChannelsMarkReadCreate,
  getGamesChannelsListQueryKey,
  getGameRetrieveQueryKey,
  ChannelMessage as ChannelMessageType,
  ChannelEvent as ChannelEventType,
} from "@/api/generated/endpoints";
import { useGameVariant } from "@/hooks/useGameVariant";

type MessageDisplayItem = {
  kind: "message";
  id: number;
  body: string;
  sender: {
    name: string;
    nationName: string | null;
    label: string;
    nationColor: string;
    picture: string | null;
    isGameMaster: boolean;
  };
  isCurrentUser: boolean;
  showAvatar: boolean;
  formattedTime: string;
};

type EventDisplayItem = {
  kind: "event";
  id: number;
  text: string;
};

type ThreadItem = MessageDisplayItem | EventDisplayItem;

const TruncatedTooltipLabel: React.FC<{
  text: string;
  className?: string;
}> = ({ text, className }) => {
  const labelRef = useRef<HTMLSpanElement>(null);
  const [isTruncated, setIsTruncated] = useState(false);
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    const label = labelRef.current;
    if (!label) return;

    const updateTruncation = () => {
      const truncated = label.scrollWidth > label.clientWidth;
      setIsTruncated(truncated);
      if (!truncated) setIsOpen(false);
    };

    updateTruncation();
    window.addEventListener("resize", updateTruncation);

    const resizeObserver =
      typeof ResizeObserver === "undefined"
        ? null
        : new ResizeObserver(updateTruncation);
    resizeObserver?.observe(label);

    return () => {
      window.removeEventListener("resize", updateTruncation);
      resizeObserver?.disconnect();
    };
  }, [text]);

  return (
    <Tooltip
      open={isTruncated ? isOpen : false}
      onOpenChange={open => setIsOpen(isTruncated && open)}
    >
      <TooltipTrigger asChild>
        <span
          ref={labelRef}
          className={cn("inline-block max-w-full truncate align-bottom", className)}
          tabIndex={isTruncated ? 0 : undefined}
          onClick={() => isTruncated && setIsOpen(true)}
        >
          {text}
        </span>
      </TooltipTrigger>
      {isTruncated && <TooltipContent side="bottom">{text}</TooltipContent>}
    </Tooltip>
  );
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

const buildThreadItems = (
  messages: readonly ChannelMessageType[],
  events: readonly ChannelEventType[]
): ThreadItem[] => {
  const entries = [
    ...messages.map(message => ({ createdAt: message.createdAt, message })),
    ...events.map(event => ({ createdAt: event.createdAt, event })),
  ].sort((a, b) => Date.parse(a.createdAt) - Date.parse(b.createdAt));

  let previousLabel: string | null = null;

  return entries.map(entry => {
    if (!("message" in entry)) {
      previousLabel = null;
      return { kind: "event", id: entry.event.id, text: entry.event.text };
    }

    const msg = entry.message;
    const label = getMessageSenderLabel(msg.sender);
    const showAvatar = previousLabel !== label;
    previousLabel = label;

    return {
      kind: "message",
      id: msg.id,
      body: msg.body,
      sender: {
        name: msg.sender.name,
        nationName: msg.sender.nation?.name ?? null,
        label,
        nationColor: msg.sender.nation?.color ?? NEUTRAL_SENDER_COLOR,
        picture: msg.sender.picture,
        isGameMaster: msg.sender.isGameMaster,
      },
      isCurrentUser: msg.sender.isCurrentUser,
      showAvatar,
      formattedTime: formatMessageTime(msg.createdAt),
    };
  });
};

const BUBBLE_ALPHA_HEX = "26"; // 15% opacity (0x26/0xFF)

const ThreadEventNotice: React.FC<{ text: string }> = ({ text }) => (
  <div className="flex justify-center py-1">
    <p className="max-w-[80%] rounded-lg border bg-background px-3 py-1 text-center text-xs font-medium text-muted-foreground shadow-xs">
      {text}
    </p>
  </div>
);

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
  const [, setSearchParams] = useSearchParams();

  const { data: game } = useGameRetrieveSuspense(gameId);
  const { data: userProfile } = useUserRetrieveSuspense();
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

  const [firstUnreadMessageId] = useState<number | null>(() => {
    const count = channel.unreadMessageCount;
    if (count <= 0) return null;
    const index = channel.messages.length - count;
    return index > 0 ? channel.messages[index].id : null;
  });

  const currentMember = game.members.find(m => m.isCurrentUser);
  const isGameMaster =
    !!game.gameMaster && game.gameMaster.userId === userProfile.userId;
  const canPost = !!currentMember || (isGameMaster && !channel.private);
  const currentNationName = currentMember?.nation ?? undefined;
  const showSenderLabels = isGroupChannel(channel, game.members, currentNationName);
  const channelDisplayName = getChannelDisplayName(channel, currentNationName);
  const channelSubtitle = getChannelSubtitle(channel, game.members, currentNationName);
  const channelTitle = (
    <div className="min-w-0 flex-1 text-left">
      <TruncatedTooltipLabel
        text={channelDisplayName}
        className="text-xl font-semibold leading-9"
      />
      {channelSubtitle && (
        <div className="leading-none">
          <TruncatedTooltipLabel
            text={channelSubtitle}
            className="text-xs leading-tight text-muted-foreground"
          />
        </div>
      )}
    </div>
  );
  const headerButtons = (
    <>
      {channel.private && currentMember && (
        <Button
          variant="outline"
          size="icon-sm"
          className="rounded-md"
          aria-label="Rename channel"
          asChild
        >
          <Link to={`/game/${gameId}/phase/${phaseId}/chat/channel/${channelId}/rename`}>
            <Pencil />
          </Link>
        </Button>
      )}
    </>
  );

  useEffect(() => {
    if (!canPost) return;
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
  }, [channel.messages, channel.events]);

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

  const threadItems = useMemo(
    () => buildThreadItems(channel.messages, channel.events),
    [channel.messages, channel.events]
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
              {threadItems.length === 0 ? (
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
                  {threadItems.map(item =>
                    item.kind === "event" ? (
                      <ThreadEventNotice key={`event-${item.id}`} text={item.text} />
                    ) : (
                      <React.Fragment key={`message-${item.id}`}>
                        {item.id === firstUnreadMessageId && <NewMessagesDivider />}
                        <Message
                          className={
                            item.isCurrentUser ? "flex-row-reverse" : undefined
                          }
                        >
                          {item.showAvatar ? (
                            <div
                              className={cn(
                                "size-8 shrink-0",
                                item.sender.isGameMaster &&
                                  "overflow-hidden rounded-full border"
                              )}
                            >
                              {item.sender.isGameMaster ? (
                                <Avatar className="size-8 rounded-none">
                                  <AvatarImage src={item.sender.picture ?? undefined} />
                                  <AvatarFallback className="rounded-none text-xs">
                                    {item.sender.name[0]?.toUpperCase() ?? "?"}
                                  </AvatarFallback>
                                </Avatar>
                              ) : (
                                <NationFlag
                                  flagUrl={
                                    variant
                                      ? findNationFlagUrl(variant.nations, item.sender.nationName)
                                      : null
                                  }
                                  alt={item.sender.nationName ?? item.sender.name}
                                  className="size-8"
                                  color={item.sender.nationColor}
                                />
                              )}
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
                              {item.showAvatar && showSenderLabels && (
                                <p
                                  className="mb-0.5 text-xs font-semibold"
                                  style={{ color: item.sender.nationColor }}
                                >
                                  {item.isCurrentUser && !item.sender.isGameMaster
                                    ? "You"
                                    : item.sender.label}
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
                    )
                  )}
                </div>
              )}
            </div>
          </Panel.Content>
          {canPost && (
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
