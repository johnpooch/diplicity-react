import React, { Suspense, useEffect, useMemo, useRef, useState } from "react";
import { useSearchParams } from "react-router";
import { useSuspenseQuery } from "@tanstack/react-query";
import { ArrowDown, Check, ChevronsUpDown, MessageCircle } from "lucide-react";

import { QueryErrorBoundary } from "@/components/QueryErrorBoundary";
import { Notice } from "@/components/Notice";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import {
  Message,
  MessageAvatar,
  MessageContent,
  MessageTimestamp,
} from "@/components/ui/message";
import { ScreenCard, ScreenCardContent } from "@/components/ui/screen-card";
import {
  fetchWatchedChannels,
  cssFeedConfigured,
  generalChannelId,
  type CssFeedChannel,
  type CssFeedMessage,
} from "@/api/cssFeed";
import { formatMessageTime } from "@/utils/formatMessageTime";

const POLL_INTERVAL_MS = 5000;
const SCROLL_BOTTOM_THRESHOLD_PX = 48;
const DISCORD_URL = "https://discord.gg/cwjzxEqTuN";
const CHANNEL_PARAM = "channel";

const openDiscord = () =>
  window.open(DISCORD_URL, "_blank", "noopener,noreferrer");

const DiscordIcon: React.FC<{ className?: string }> = ({ className }) => (
  <svg
    role="img"
    viewBox="0 0 24 24"
    xmlns="http://www.w3.org/2000/svg"
    className={className}
    fill="currentColor"
    aria-label="Discord"
  >
    <path d="M20.317 4.37a19.791 19.791 0 0 0-4.885-1.515.074.074 0 0 0-.079.037c-.21.375-.444.864-.608 1.25a18.27 18.27 0 0 0-5.487 0 12.64 12.64 0 0 0-.617-1.25.077.077 0 0 0-.079-.037A19.736 19.736 0 0 0 3.677 4.37a.07.07 0 0 0-.032.027C.533 9.046-.32 13.58.099 18.057a.082.082 0 0 0 .031.057 19.9 19.9 0 0 0 5.993 3.03.078.078 0 0 0 .084-.028 14.09 14.09 0 0 0 1.226-1.994.076.076 0 0 0-.041-.106 13.107 13.107 0 0 1-1.872-.892.077.077 0 0 1-.008-.128 10.2 10.2 0 0 0 .372-.292.074.074 0 0 1 .077-.01c3.928 1.793 8.18 1.793 12.062 0a.074.074 0 0 1 .078.01c.12.098.246.198.373.292a.077.077 0 0 1-.006.127 12.299 12.299 0 0 1-1.873.892.077.077 0 0 0-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 0 0 .084.028 19.839 19.839 0 0 0 6.002-3.03.077.077 0 0 0 .032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 0 0-.031-.03zM8.02 15.33c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.956-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.956 2.418-2.157 2.418zm7.975 0c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.955-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.946 2.418-2.157 2.418z" />
  </svg>
);

const MoreMessagesNotice: React.FC = () => (
  <div className="flex justify-center py-1">
    <button
      type="button"
      onClick={openDiscord}
      className="max-w-[80%] rounded-lg border bg-background px-3 py-1 text-center text-xs font-medium text-muted-foreground shadow-xs hover:bg-accent hover:text-accent-foreground"
    >
      More messages on Discord
    </button>
  </div>
);

type MessageDisplayItem = {
  id: string;
  content: string;
  authorName: string;
  authorAvatar: string | null;
  formattedTime: string;
  showAuthor: boolean;
  attachments: CssFeedMessage["attachments"];
};

const buildMessageItems = (
  messages: readonly CssFeedMessage[]
): MessageDisplayItem[] =>
  messages.map((message, index) => ({
    id: message.id,
    content: message.content,
    authorName: message.authorName,
    authorAvatar: message.authorAvatar,
    formattedTime: formatMessageTime(message.createdAt),
    showAuthor: index === 0 || messages[index - 1].authorId !== message.authorId,
    attachments: message.attachments,
  }));

const CommunityChatSkeleton: React.FC = () => (
  <div className="flex flex-1 min-h-0 flex-col space-y-4">
    <div className="flex items-center justify-between gap-3">
      <div className="flex items-center gap-3">
        <DiscordIcon className="size-5" />
        <h2 className="text-lg font-semibold">Join our discord</h2>
      </div>
      <Skeleton className="h-8 w-24" />
    </div>
    <div className="flex flex-1 min-h-0 flex-col gap-3">
      {[0, 1, 2].map(i => (
        <div key={i} className="flex gap-3">
          <Skeleton className="size-8 rounded-full shrink-0" />
          <div className="flex flex-col gap-1.5 flex-1">
            <Skeleton className="h-3 w-24" />
            <Skeleton className="h-8 w-2/3 rounded-lg" />
          </div>
        </div>
      ))}
    </div>
  </div>
);

interface ChannelSwitcherProps {
  channels: readonly CssFeedChannel[];
  selectedChannelId: string | undefined;
  onSelect: (channelId: string) => void;
}

const ChannelSwitcher: React.FC<ChannelSwitcherProps> = ({
  channels,
  selectedChannelId,
  onSelect,
}) => {
  const [open, setOpen] = useState(false);
  const selected = channels.find(c => c.id === selectedChannelId);

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <button
          type="button"
          aria-label={`${selected?.name ?? "Select channel"}. Choose channel`}
          className="group flex items-center gap-1 rounded-md px-2 py-1 text-sm text-muted-foreground hover:bg-accent hover:text-accent-foreground"
        >
          <span className="truncate">#{selected?.name}</span>
          <ChevronsUpDown className="size-4 shrink-0" />
        </button>
      </PopoverTrigger>
      <PopoverContent align="end" className="w-56 p-1">
        <div className="flex max-h-80 flex-col overflow-y-auto">
          {channels.map(channel => (
            <button
              key={channel.id}
              type="button"
              className="flex w-full items-center gap-2 rounded-sm px-2 py-1.5 text-left hover:bg-accent hover:text-accent-foreground"
              onClick={() => {
                onSelect(channel.id);
                setOpen(false);
              }}
            >
              <span className="min-w-0 flex-1 truncate text-sm font-medium">
                #{channel.name}
              </span>
              {channel.id === selectedChannelId && (
                <Check className="size-4 shrink-0" aria-hidden />
              )}
            </button>
          ))}
        </div>
      </PopoverContent>
    </Popover>
  );
};

const CommunityChatBody: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();

  const { data: channels } = useSuspenseQuery({
    queryKey: ["css-feed", "feed"],
    queryFn: fetchWatchedChannels,
    refetchInterval: POLL_INTERVAL_MS,
    refetchIntervalInBackground: false,
  });

  const requestedChannelId = searchParams.get(CHANNEL_PARAM);
  const selectedChannel =
    channels.find(c => c.id === requestedChannelId) ??
    channels.find(c => c.id === generalChannelId) ??
    channels[0];

  const handleSelectChannel = (channelId: string) => {
    setSearchParams(
      prev => {
        const next = new URLSearchParams(prev);
        next.set(CHANNEL_PARAM, channelId);
        return next;
      },
      { replace: true }
    );
  };

  const messageItems = useMemo(
    () => buildMessageItems(selectedChannel?.messages ?? []),
    [selectedChannel]
  );

  const messagesContainerRef = useRef<HTMLDivElement>(null);
  const isNearBottomRef = useRef(true);
  const lastMessageIdRef = useRef<string | null>(null);
  const previousChannelIdRef = useRef<string | undefined>(undefined);
  const [hasNewMessages, setHasNewMessages] = useState(false);

  const scrollToBottom = (smooth = false) => {
    const el = messagesContainerRef.current;
    if (!el) return;
    if (smooth && typeof el.scrollTo === "function") {
      el.scrollTo({ top: el.scrollHeight, behavior: "smooth" });
    } else {
      el.scrollTop = el.scrollHeight;
    }
    isNearBottomRef.current = true;
    setHasNewMessages(false);
  };

  const handleScroll = () => {
    const el = messagesContainerRef.current;
    if (!el) return;
    const distanceFromBottom = el.scrollHeight - el.scrollTop - el.clientHeight;
    isNearBottomRef.current = distanceFromBottom < SCROLL_BOTTOM_THRESHOLD_PX;
    if (isNearBottomRef.current) setHasNewMessages(false);
  };

  useEffect(() => {
    const lastItem = messageItems[messageItems.length - 1];
    const channelChanged = previousChannelIdRef.current !== selectedChannel?.id;
    previousChannelIdRef.current = selectedChannel?.id;

    if (channelChanged) {
      lastMessageIdRef.current = lastItem?.id ?? null;
      scrollToBottom();
      return;
    }

    const isNewMessage = !!lastItem && lastItem.id !== lastMessageIdRef.current;
    lastMessageIdRef.current = lastItem?.id ?? null;
    if (!isNewMessage) return;

    if (isNearBottomRef.current) {
      scrollToBottom();
    } else {
      setHasNewMessages(true);
    }
  }, [messageItems, selectedChannel?.id]);

  return (
    <div className="flex flex-1 min-h-0 flex-col space-y-4">
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <DiscordIcon className="size-5" />
          <h2 className="text-lg font-semibold">Join our discord</h2>
        </div>
        {channels.length > 0 && (
          <ChannelSwitcher
            channels={channels}
            selectedChannelId={selectedChannel?.id}
            onSelect={handleSelectChannel}
          />
        )}
      </div>

      {messageItems.length === 0 ? (
        <Notice
          icon={MessageCircle}
          title="No messages yet"
          message={
            selectedChannel
              ? `Nothing has been said in #${selectedChannel.name} yet`
              : undefined
          }
          className="flex-1"
        />
      ) : (
        <div className="relative flex-1 min-h-0">
          <div
            ref={messagesContainerRef}
            onScroll={handleScroll}
            className="flex h-full flex-col gap-2 overflow-y-auto"
          >
            <MoreMessagesNotice />
            {messageItems.map(item => (
              <Message key={item.id}>
                {item.showAuthor ? (
                  <MessageAvatar
                    src={item.authorAvatar ?? undefined}
                    alt={item.authorName}
                    fallback={item.authorName[0]?.toUpperCase() ?? "?"}
                  />
                ) : (
                  <div className="w-8 shrink-0" />
                )}
                <MessageContent className={item.showAuthor ? "rounded-tl-none" : undefined}>
                  {item.content}
                  {item.attachments.map(attachment =>
                    attachment.contentType?.startsWith("image/") ? (
                      <img
                        key={attachment.url}
                        src={attachment.url}
                        alt={attachment.name}
                        className="mt-1 max-h-48 rounded-md"
                      />
                    ) : (
                      <a
                        key={attachment.url}
                        href={attachment.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="mt-1 block text-sm underline"
                      >
                        {attachment.name}
                      </a>
                    )
                  )}
                  {item.showAuthor ? (
                    <div className="flex items-center justify-between gap-2 mt-0.5">
                      <span className="text-xs font-medium text-foreground/50">
                        {item.authorName}
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
            ))}
          </div>
          {hasNewMessages && (
            <Button
              onClick={() => scrollToBottom(true)}
              size="sm"
              className="absolute bottom-2 left-1/2 -translate-x-1/2 rounded-full shadow-md"
            >
              <ArrowDown className="size-3.5" />
              New messages
            </Button>
          )}
        </div>
      )}
    </div>
  );
};

const CommunityChat: React.FC = () => {
  if (!cssFeedConfigured) return null;

  return (
    <ScreenCard className="flex-1 min-h-0">
      <ScreenCardContent className="flex flex-1 min-h-0 flex-col space-y-4">
        <QueryErrorBoundary
          reportErrors={false}
          fallback={
            <div className="flex flex-1 flex-col justify-center space-y-4">
              <div className="flex items-center gap-3">
                <DiscordIcon className="size-5" />
                <h2 className="text-lg font-semibold">Join the community</h2>
              </div>
              <p className="text-sm text-muted-foreground">
                Chat with fellow Diplomacy players, find open games, and jump
                into strategy discussions on our Discord server. Whether
                you're new to the game or a seasoned veteran, there's a place
                for you — and you can chat directly with the developers.
              </p>
            </div>
          }
        >
          <Suspense fallback={<CommunityChatSkeleton />}>
            <CommunityChatBody />
          </Suspense>
        </QueryErrorBoundary>
        <Button onClick={openDiscord} className="w-full">
          <DiscordIcon className="size-4" />
          Join the discussion
        </Button>
      </ScreenCardContent>
    </ScreenCard>
  );
};

export { CommunityChat };
