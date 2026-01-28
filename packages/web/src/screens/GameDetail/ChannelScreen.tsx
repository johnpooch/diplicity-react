import React, { Suspense, useState, useRef, useEffect } from "react";
import { useNavigate } from "react-router";
import { useQueryClient } from "@tanstack/react-query";
import { Send, MessageCircle } from "lucide-react";
import { useRequiredParams } from "@/hooks";
import { toast } from "sonner";

import { QueryErrorBoundary } from "@/components/QueryErrorBoundary";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Separator } from "@/components/ui/separator";
import {
  Message,
  MessageContent,
  MessageTimestamp,
} from "@/components/ui/message";
import { Notice } from "@/components/Notice";
import { NationFlag } from "@/components/NationFlag";
import { GameDetailAppBar } from "./AppBar";
import { Panel } from "@/components/Panel";
import {
  useGameRetrieveSuspense,
  useGamesChannelsListSuspense,
  useVariantsListSuspense,
  useGamesChannelsMessagesCreateCreate,
  getGamesChannelsListQueryKey,
  ChannelMessage as ChannelMessageType,
} from "@/api/generated/endpoints";

type MessageDisplayItem = {
  id: number;
  body: string;
  createdAt: string;
  sender: {
    nationName: string;
    picture: string | null;
  };
  isCurrentUser: boolean;
  showAvatar: boolean;
  formattedTime: string;
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
        picture: msg.sender.picture,
      },
      isCurrentUser: msg.sender.isCurrentUser,
      showAvatar,
      formattedTime: new Date(msg.createdAt).toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
      }),
    };
  });
};

const ChannelScreen: React.FC = () => {
  const { gameId, phaseId, channelId } = useRequiredParams<{
    gameId: string;
    phaseId: string;
    channelId: string;
  }>();

  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [message, setMessage] = useState("");

  const { data: game } = useGameRetrieveSuspense(gameId);
  const { data: channels } = useGamesChannelsListSuspense(gameId);
  const { data: variants } = useVariantsListSuspense();
  const createMessageMutation = useGamesChannelsMessagesCreateCreate();

  const messagesContainerRef = useRef<HTMLDivElement>(null);

  const channel = channels.find(c => c.id === parseInt(channelId));
  if (!channel) throw new Error("Channel not found");

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

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const variant = variants.find(v => v.id === game.variantId);
  const variantId = variant?.id;

  const messageItems = buildMessageItems(channel.messages);

  return (
    <div className="flex flex-col flex-1 min-h-0">
      <GameDetailAppBar
        title={channel.name}
        onNavigateBack={() => navigate(`/game/${gameId}/phase/${phaseId}/chat`)}
        variant="secondary"
      />
      <div className="flex-1 overflow-y-auto">
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
                  {messageItems.map(item => (
                    <Message
                      key={item.id}
                      className={
                        item.isCurrentUser ? "flex-row-reverse" : undefined
                      }
                    >
                      {item.showAvatar ? (
                        <div className="flex flex-col items-center gap-0.5">
                          <NationFlag
                            nation={item.sender.nationName}
                            variantId={variantId!}
                            size="lg"
                          />
                          <span className="text-xs text-muted-foreground">
                            {item.sender.nationName}
                          </span>
                        </div>
                      ) : (
                        <div className="w-8" />
                      )}
                      <MessageContent>
                        {item.body}
                        <MessageTimestamp>
                          {item.formattedTime}
                        </MessageTimestamp>
                      </MessageContent>
                    </Message>
                  ))}
                </div>
              )}
            </div>
          </Panel.Content>
          <Separator />
          <Panel.Footer>
            <div className="flex gap-2 w-full">
              <Input
                placeholder="Type a message"
                value={message}
                onChange={e => setMessage(e.target.value)}
                onKeyDown={handleKeyDown}
                disabled={createMessageMutation.isPending}
                className="flex-1"
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
