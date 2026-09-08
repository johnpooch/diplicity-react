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
import { nationColours } from "@/components/NationAvatar";
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
  showName: boolean;
}> = ({ message, showIdentity, showName }) => {
  return (
    <Message
      className={cn(message.isCurrentUser && "flex-row-reverse")}
    >
      {showIdentity ? (
        <div className="size-8 shrink-0 overflow-hidden rounded-full border">
          <NationFlag nation={message.nation} />
        </div>
      ) : (
        <div className="size-8 shrink-0" />
      )}
      <div className="max-w-[80%]">
        <MessageContent
          className={cn(nationColours[message.nation] ?? "bg-secondary")}
        >
          {showName && (
            <p className="mb-0.5 text-xs font-semibold">
              {message.isCurrentUser ? "You" : message.nation}
            </p>
          )}
          {message.body}
        </MessageContent>
        <MessageTimestamp
          className={cn(!message.isCurrentUser && "text-left")}
        >
          {message.sentAt}
        </MessageTimestamp>
      </div>
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
        const showIdentity = !previous || !isMessage(previous)
          || previous.nation !== entry.nation;
        const showName = thread.kind === "group" && showIdentity;

        return (
          <Bubble
            key={entry.id}
            message={entry}
            showIdentity={showIdentity}
            showName={showName}
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
