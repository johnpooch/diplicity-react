import React, {
  Suspense,
  useRef,
  useEffect,
  useLayoutEffect,
  useState,
  useMemo,
} from "react";
import { Link, useNavigate, useSearchParams } from "react-router";
import { useQueryClient } from "@tanstack/react-query";
import { ChevronRight, SendHorizontal, MessageCircle, MessageSquareOff } from "lucide-react";
import { useDraft, useRequiredParams } from "@/hooks";
import { useIsDesktopWeb } from "@/hooks/use-platform";
import { useChannelMessages } from "@/hooks/useChannelMessages";
import { useInfiniteScroll } from "@/hooks/useInfiniteScroll";
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
  useGamesChannelsRetrieveSuspense,
  useGamesChannelsMessagesCreateCreate,
  useGamesChannelsMarkReadCreate,
  getGamesChannelsRetrieveQueryKey,
  getGamesChannelPreviewsListQueryKey,
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

interface ThreadMessageProps {
  item: MessageDisplayItem;
  showSenderLabel: boolean;
  flagUrl: string | null;
}

const ThreadMessage: React.FC<ThreadMessageProps> = ({
  item,
  showSenderLabel,
  flagUrl,
}) => (
  <Message className={item.isCurrentUser ? "flex-row-reverse" : undefined}>
    {item.showAvatar ? (
      <div
        className={cn(
          "size-8 shrink-0",
          item.sender.isGameMaster && "overflow-hidden rounded-full border"
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
            flagUrl={flagUrl}
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
        {item.showAvatar && showSenderLabel && (
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
);

const threadItemKey = (item: ThreadItem) => `${item.kind}-${item.id}`;

const isScrolledToBottom = (element: HTMLElement) =>
  element.scrollHeight - element.scrollTop - element.clientHeight < 8;

interface ChannelThreadProps {
  items: ThreadItem[];
  unreadDivider: number | "top" | null;
  hasOlder: boolean;
  isFetchingOlder: boolean;
  isFetchOlderError: boolean;
  fetchOlder: () => void;
  scrollToBottomOnAppendRef: React.RefObject<boolean>;
  renderMessage: (item: MessageDisplayItem) => React.ReactNode;
}

const ChannelThread: React.FC<ChannelThreadProps> = ({
  items,
  unreadDivider,
  hasOlder,
  isFetchingOlder,
  isFetchOlderError,
  fetchOlder,
  scrollToBottomOnAppendRef,
  renderMessage,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const isAtBottomRef = useRef(true);
  const previousRef = useRef<{
    firstKey: string;
    lastKey: string;
    scrollHeight: number;
  } | null>(null);
  const sentinelRef = useInfiniteScroll(
    fetchOlder,
    hasOlder && !isFetchOlderError,
    isFetchingOlder
  );

  const firstKey = threadItemKey(items[0]);
  const lastKey = threadItemKey(items[items.length - 1]);

  useLayoutEffect(() => {
    const container = containerRef.current;
    if (!container) return;
    const previous = previousRef.current;
    if (!previous) {
      container.scrollTop = container.scrollHeight;
    } else if (previous.lastKey !== lastKey) {
      if (isAtBottomRef.current || scrollToBottomOnAppendRef.current) {
        container.scrollTop = container.scrollHeight;
        scrollToBottomOnAppendRef.current = false;
      }
    } else if (previous.firstKey !== firstKey) {
      container.scrollTop += container.scrollHeight - previous.scrollHeight;
    }
    isAtBottomRef.current = isScrolledToBottom(container);
    previousRef.current = {
      firstKey,
      lastKey,
      scrollHeight: container.scrollHeight,
    };
  }, [firstKey, lastKey, scrollToBottomOnAppendRef]);

  return (
    <div
      ref={containerRef}
      onScroll={event => {
        isAtBottomRef.current = isScrolledToBottom(event.currentTarget);
      }}
      className="flex-1 min-h-0 overflow-y-auto [overflow-anchor:none] flex flex-col gap-3 px-3 py-4"
    >
      {hasOlder &&
        (isFetchOlderError ? (
          <Button
            variant="ghost"
            size="sm"
            className="self-center"
            onClick={() => fetchOlder()}
            disabled={isFetchingOlder}
          >
            Load earlier messages
          </Button>
        ) : (
          <div ref={sentinelRef} />
        ))}
      {unreadDivider === "top" && <NewMessagesDivider />}
      {items.map(item =>
        item.kind === "event" ? (
          <ThreadEventNotice key={threadItemKey(item)} text={item.text} />
        ) : (
          <React.Fragment key={threadItemKey(item)}>
            {item.id === unreadDivider && <NewMessagesDivider />}
            {renderMessage(item)}
          </React.Fragment>
        )
      )}
    </div>
  );
};

const ChannelScreen: React.FC = () => {
  const { gameId, phaseId, channelId } = useRequiredParams<{
    gameId: string;
    phaseId: string;
    channelId: string;
  }>();
  const numericChannelId = parseInt(channelId);

  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const isDesktopWeb = useIsDesktopWeb();
  const [message, setMessage, getOrCreateDraftId] = useDraft(gameId, channelId);
  const [, setSearchParams] = useSearchParams();

  const { data: game } = useGameRetrieveSuspense(gameId);
  const { data: userProfile } = useUserRetrieveSuspense();
  const { data: channel } = useGamesChannelsRetrieveSuspense(
    gameId,
    numericChannelId,
    { query: { refetchInterval: 5000 } }
  );
  const { messages, hasOlder, fetchOlder, isFetchingOlder, isFetchOlderError } =
    useChannelMessages(gameId, numericChannelId, channel.latestMessageId);
  const variant = useGameVariant(game);
  const createMessageMutation = useGamesChannelsMessagesCreateCreate({
    mutation: { retry: 2 },
  });
  const markReadMutation = useGamesChannelsMarkReadCreate();

  const isSendingRef = useRef(false);
  const scrollToBottomOnAppendRef = useRef(false);
  const [firstUnreadMessageId] = useState(channel.firstUnreadMessageId);

  useEffect(() => {
    setSearchParams(prev => {
      const next = new URLSearchParams(prev);
      next.set("channelId", channelId);
      return next;
    }, { replace: true });
  }, [channelId, setSearchParams]);

  const currentMember = game.members.find(m => m.isCurrentUser);
  const isGameMaster =
    !!game.gameMaster && game.gameMaster.userId === userProfile.userId;
  const canPost = !!currentMember || (isGameMaster && !channel.private);
  const currentNationName = currentMember?.nation ?? undefined;
  const showSenderLabels = isGroupChannel(channel, game.members, currentNationName);
  const channelDisplayName = getChannelDisplayName(channel, currentNationName);
  const channelSubtitle = getChannelSubtitle(channel, game.members, currentNationName);
  const channelTitleContent = (
    <>
      <div className="flex min-w-0 items-center gap-1">
        <TruncatedTooltipLabel
          text={channelDisplayName}
          className="min-w-0 text-xl font-semibold leading-9"
        />
        <ChevronRight className="size-4 shrink-0 text-muted-foreground" />
      </div>
      {channelSubtitle && (
        <div className="leading-none">
          <TruncatedTooltipLabel
            text={channelSubtitle}
            className="text-xs leading-tight text-muted-foreground"
          />
        </div>
      )}
    </>
  );
  const channelTitle = (
    <Link
      to={`/game/${gameId}/phase/${phaseId}/chat/channel/${channelId}/options`}
      className="block min-w-0 flex-1 rounded-md text-left outline-none focus-visible:ring-2 focus-visible:ring-ring"
      aria-label={`Open chat options for ${channelDisplayName}`}
    >
      {channelTitleContent}
    </Link>
  );

  useEffect(() => {
    if (!canPost) return;
    markReadMutation.mutateAsync({
      gameId,
      channelId: numericChannelId,
    }).then(() => {
      queryClient.invalidateQueries({
        queryKey: getGamesChannelsRetrieveQueryKey(gameId, numericChannelId),
      });
      queryClient.invalidateQueries({
        queryKey: getGamesChannelPreviewsListQueryKey(gameId),
      });
      queryClient.invalidateQueries({
        queryKey: getGameRetrieveQueryKey(gameId),
      });
    }).catch(() => {
      // Fire-and-forget: silently ignore mark-read failures
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps -- mutation object excluded per project convention (not referentially stable); fire once on mount
  }, [gameId, channelId]);

  const handleSubmit = async () => {
    if (!message.trim() || isSendingRef.current) return;
    isSendingRef.current = true;

    try {
      await createMessageMutation.mutateAsync({
        gameId,
        channelId: numericChannelId,
        data: { body: message, clientMessageId: getOrCreateDraftId() },
      });
      setMessage("");
      scrollToBottomOnAppendRef.current = true;
      queryClient.invalidateQueries({
        queryKey: getGamesChannelsRetrieveQueryKey(gameId, numericChannelId),
      });
      queryClient.invalidateQueries({
        queryKey: getGamesChannelPreviewsListQueryKey(gameId),
      });
    } catch {
      toast.error("Failed to send message");
    } finally {
      isSendingRef.current = false;
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

  const oldestLoadedMessage = messages[0];
  const threadItems = useMemo(
    () =>
      buildThreadItems(
        messages,
        hasOlder && oldestLoadedMessage
          ? channel.events.filter(
              event =>
                Date.parse(event.createdAt) >=
                Date.parse(oldestLoadedMessage.createdAt)
            )
          : channel.events
      ),
    [messages, channel.events, hasOlder, oldestLoadedMessage]
  );

  const unreadDivider =
    firstUnreadMessageId === null
      ? null
      : messages.some(item => item.id === firstUnreadMessageId)
        ? firstUnreadMessageId
        : hasOlder &&
            messages.every(item => item.id > firstUnreadMessageId)
          ? "top"
          : null;

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
              {threadItems.length === 0 ? (
                <Notice
                  icon={MessageCircle}
                  title="No messages yet"
                  message="Start the conversation by sending a message"
                  className="h-full"
                />
              ) : (
                <ChannelThread
                  items={threadItems}
                  unreadDivider={unreadDivider}
                  hasOlder={hasOlder}
                  isFetchingOlder={isFetchingOlder}
                  isFetchOlderError={isFetchOlderError}
                  fetchOlder={fetchOlder}
                  scrollToBottomOnAppendRef={scrollToBottomOnAppendRef}
                  renderMessage={item => (
                    <ThreadMessage
                      item={item}
                      showSenderLabel={showSenderLabels}
                      flagUrl={
                        variant
                          ? findNationFlagUrl(variant.nations, item.sender.nationName)
                          : null
                      }
                    />
                  )}
                />
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
                  aria-label="Send message"
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

const ChannelScreenSuspense: React.FC = () => {
  const { gameId, channelId } = useRequiredParams<{
    gameId: string;
    channelId: string;
  }>();

  return (
    <QueryErrorBoundary key={`${gameId}/${channelId}`}>
      <Suspense fallback={<div></div>}>
        <ChannelScreen />
      </Suspense>
    </QueryErrorBoundary>
  );
};

export { ChannelScreenSuspense as ChannelScreen };
