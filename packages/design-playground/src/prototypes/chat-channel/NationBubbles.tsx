import { useEffect, useRef } from "react";
import { Button } from "@/components/ui/button";
import {
  Empty,
  EmptyDescription,
  EmptyHeader,
  EmptyMedia,
  EmptyTitle,
} from "@/components/ui/empty";
import { Input } from "@/components/ui/input";
import {
  Message,
  MessageContent,
  MessageTimestamp,
} from "@/components/ui/message";
import { GameDetailShell } from "@/components/GameDetailShell";
import { NationFlag } from "@/components/NationFlag";
import {
  franceDirectEmpty,
  franceDirectMany,
  franceDirectOne,
  greatAllianceMany,
  greatAllianceOne,
} from "@/data/fixtures";
import type { ChatEntry, ChatMessage, ChatThread } from "@/data/types";
import { cn } from "@/lib/utils";
import { Map, MessagesSquare, SendHorizontal } from "lucide-react";

const nationHex: Record<string, string> = {
  Austria: "#F44336",
  England: "#2196F3",
  France: "#80DEEA",
  Germany: "#90A4AE",
  Italy: "#4CAF50",
  Russia: "#F5F5F5",
  Turkey: "#FFC107",
};

const BUBBLE_ALPHA_HEX = "26";

const toHex6 = (color: string): string => {
  const short = /^#([0-9a-fA-F])([0-9a-fA-F])([0-9a-fA-F])$/.exec(color);
  if (short) {
    return `#${short[1]}${short[1]}${short[2]}${short[2]}${short[3]}${short[3]}`;
  }
  if (/^#[0-9a-fA-F]{6}$/.test(color)) return color;
  return "#808080";
};

const brightnessByColor = (hex: string): number => {
  const match = /^#([0-9a-fA-F]{2})([0-9a-fA-F]{2})([0-9a-fA-F]{2})$/.exec(
    toHex6(hex)
  );
  if (!match) return 128;
  const r = parseInt(match[1], 16);
  const g = parseInt(match[2], 16);
  const b = parseInt(match[3], 16);
  return (r * 299 + g * 587 + b * 114) / 1000;
};

const chatListPath = "/chat-channel-list/single-list/active";

const threads: Record<string, ChatThread> = {
  empty: franceDirectEmpty,
  one: franceDirectOne,
  direct: franceDirectMany,
  "group-one": greatAllianceOne,
  group: greatAllianceMany,
};

const isMessage = (entry: ChatEntry): entry is ChatMessage =>
  entry.type === "message";

const PhaseMarker: React.FC<{ label: string }> = ({ label }) => {
  return (
    <div className="flex justify-center py-1">
      <p className="rounded-lg border bg-background px-3 py-1 text-xs font-medium text-muted-foreground shadow-xs">
        {label}
      </p>
    </div>
  );
};

const Bubble: React.FC<{
  message: ChatMessage;
  showIdentity: boolean;
}> = ({ message, showIdentity }) => {
  const color = nationHex[message.nation] ?? "#808080";

  return (
    <Message className={cn(message.isCurrentUser && "flex-row-reverse")}>
      {showIdentity ? (
        <div className="size-8 shrink-0 overflow-hidden rounded-full border">
          <NationFlag nation={message.nation} />
        </div>
      ) : (
        <div className="size-8 shrink-0" />
      )}
      <MessageContent
        className={cn(
          "max-w-[80%] py-1.5 px-2",
          message.isCurrentUser ? "rounded-tr-none" : "rounded-tl-none"
        )}
        style={{
          backgroundColor: toHex6(color) + BUBBLE_ALPHA_HEX,
          border:
            brightnessByColor(color) > 128 ? `1px solid ${color}` : undefined,
        }}
      >
        {message.body}
        {showIdentity ? (
          <div className="mt-0.5 flex items-center justify-between gap-2">
            <span className="text-xs font-medium" style={{ color }}>
              {message.nation}
            </span>
            <span className="text-xs text-muted-foreground">
              {message.sentAt}
            </span>
          </div>
        ) : (
          <MessageTimestamp className="mt-0.5">
            {message.sentAt}
          </MessageTimestamp>
        )}
      </MessageContent>
    </Message>
  );
};

const Thread: React.FC<{ thread: ChatThread }> = ({ thread }) => {
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView();
  }, [thread.id]);

  const hasMessages = thread.entries.some(isMessage);

  return (
    <div className="flex flex-col gap-3">
      {thread.entries.map((entry, index) => {
        if (entry.type === "phase") {
          return <PhaseMarker key={entry.id} label={entry.label} />;
        }

        const previous = index > 0 ? thread.entries[index - 1] : undefined;
        const showIdentity =
          !previous || !isMessage(previous) || previous.nation !== entry.nation;

        return (
          <Bubble
            key={entry.id}
            message={entry}
            showIdentity={showIdentity}
          />
        );
      })}
      {!hasMessages && (
        <Empty>
          <EmptyHeader>
            <EmptyMedia variant="icon">
              <MessagesSquare />
            </EmptyMedia>
            <EmptyTitle>No messages yet</EmptyTitle>
            <EmptyDescription>
              Nobody has written in this channel.
            </EmptyDescription>
          </EmptyHeader>
        </Empty>
      )}
      <div ref={endRef} />
    </div>
  );
};

const ChatChannel: React.FC<{ state: string }> = ({ state }) => {
  const thread = threads[state] ?? threads.direct;

  return (
    <GameDetailShell
      title={thread.name}
      subtitle={thread.subtitle}
      activeNavItem="Chat"
      mode="secondary"
      backTo={chatListPath}
      headerAction={
        <Button
          variant="outline"
          size="icon-sm"
          className="rounded-full md:hidden"
          aria-label="Map preview"
        >
          <Map />
        </Button>
      }
      footer={
        <div className="flex items-center gap-2 px-2 py-2 md:px-3">
          <Input placeholder="Type a message..." />
          <Button size="icon" aria-label="Send">
            <SendHorizontal />
          </Button>
        </div>
      }
    >
      <Thread thread={thread} />
    </GameDetailShell>
  );
};

export { ChatChannel };
