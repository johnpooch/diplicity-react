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
import { GameShell } from "@/components/GameShell";
import { NationAvatar } from "@/components/NationAvatar";
import { channel, emptyChannel } from "@/data/fixtures";
import { cn } from "@/lib/utils";
import { MessagesSquare, SendHorizontal } from "lucide-react";

const Channel: React.FC<{ state: string }> = ({ state }) => {
  const data = state === "empty" ? emptyChannel : channel;

  return (
    <GameShell
      title="The Congress of Vienna"
      subtitle="Spring 1903 Movement"
      activeNavItem="Chat"
    >
      <div className="flex items-center gap-2 border-b px-3 py-2">
        <div className="flex -space-x-1">
          {data.members.map(nation => (
            <NationAvatar
              key={nation}
              nation={nation}
              className="size-7 ring-2 ring-background"
            />
          ))}
        </div>
        <p className="truncate text-sm font-medium">{data.name}</p>
      </div>

      <div className="flex-1 overflow-y-auto p-3">
        {data.messages.length === 0 ? (
          <Empty>
            <EmptyHeader>
              <EmptyMedia variant="icon">
                <MessagesSquare />
              </EmptyMedia>
              <EmptyTitle>No messages yet</EmptyTitle>
              <EmptyDescription>
                Nobody has written in this channel. Someone has to go first.
              </EmptyDescription>
            </EmptyHeader>
          </Empty>
        ) : (
          <div className="flex flex-col gap-3">
            {data.messages.map(message => (
              <Message
                key={message.id}
                className={cn(
                  message.isCurrentUser && "flex-row-reverse"
                )}
              >
                <NationAvatar nation={message.nation} />
                <div className="max-w-[80%]">
                  <MessageContent
                    className={cn(
                      message.isCurrentUser &&
                        "bg-primary text-primary-foreground"
                    )}
                  >
                    {!message.isCurrentUser && (
                      <p className="mb-0.5 text-xs font-semibold">
                        {message.nation}
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
            ))}
          </div>
        )}
      </div>

      <div className="flex items-center gap-2 border-t p-3">
        <Input placeholder="Message Austria, England, Russia" />
        <Button size="icon" aria-label="Send">
          <SendHorizontal />
        </Button>
      </div>
    </GameShell>
  );
};

export { Channel };
