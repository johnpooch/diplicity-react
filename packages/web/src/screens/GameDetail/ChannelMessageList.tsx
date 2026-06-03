import React from "react";
import { MessageCircle } from "lucide-react";
import { Message, MessageContent, MessageTimestamp } from "@/components/ui/message";
import { Notice } from "@/components/Notice";
import { NationFlag, findNationFlagUrl } from "@/components/NationFlag";
import { brightnessByColor, toHex6 } from "./channelUtils";
import { ChannelMessage as ChannelMessageType } from "@/api/generated/endpoints";

const BUBBLE_ALPHA_HEX = "26";

export type MessageDisplayItem = {
  id: number;
  body: string;
  sender: { nationName: string; nationColor: string };
  isCurrentUser: boolean;
  showAvatar: boolean;
  formattedTime: string;
};

export const formatMessageTime = (createdAt: string): string => {
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

export const buildMessageDisplayItems = (
  messages: readonly ChannelMessageType[]
): MessageDisplayItem[] =>
  messages.map((msg, index) => ({
    id: msg.id,
    body: msg.body,
    sender: {
      nationName: msg.sender.nation.name,
      nationColor: msg.sender.nation.color,
    },
    isCurrentUser: msg.sender.isCurrentUser,
    showAvatar:
      index === 0 || messages[index - 1].sender.nation.name !== msg.sender.nation.name,
    formattedTime: formatMessageTime(msg.createdAt),
  }));

const NewMessagesDivider: React.FC = () => (
  <div className="flex items-center gap-2 my-1">
    <div className="flex-1 h-px bg-border" />
    <span className="text-xs text-muted-foreground font-medium">New messages</span>
    <div className="flex-1 h-px bg-border" />
  </div>
);

interface ChannelMessageListProps {
  messageItems: MessageDisplayItem[];
  variantNations: ReadonlyArray<{ name: string; flagUrl: string | null }>;
  firstUnreadIndex?: number | null;
  scrollContainerRef?: React.RefObject<HTMLDivElement>;
  emptyMessage?: string;
}

export const ChannelMessageList: React.FC<ChannelMessageListProps> = ({
  messageItems,
  variantNations,
  firstUnreadIndex,
  scrollContainerRef,
  emptyMessage,
}) => {
  if (messageItems.length === 0) {
    return (
      <Notice
        icon={MessageCircle}
        title="No messages yet"
        message={emptyMessage}
        className="h-full"
      />
    );
  }

  return (
    <div
      ref={scrollContainerRef}
      className="flex-1 min-h-0 overflow-y-auto flex flex-col gap-2 p-2"
    >
      {messageItems.map((item, index) => (
        <React.Fragment key={item.id}>
          {firstUnreadIndex != null && index === firstUnreadIndex && (
            <NewMessagesDivider />
          )}
          <Message className={item.isCurrentUser ? "flex-row-reverse" : undefined}>
            {item.showAvatar ? (
              <div className="w-8 flex-shrink-0 flex justify-center">
                <NationFlag
                  flagUrl={findNationFlagUrl(variantNations, item.sender.nationName)}
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
                border:
                  brightnessByColor(item.sender.nationColor) > 128
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
                <MessageTimestamp className="mt-0.5">{item.formattedTime}</MessageTimestamp>
              )}
            </MessageContent>
          </Message>
        </React.Fragment>
      ))}
    </div>
  );
};
