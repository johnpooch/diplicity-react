import React, { Suspense } from "react";
import { Link } from "react-router";
import { UserPlus, MessageSquare } from "lucide-react";
import { useRequiredParams } from "@/hooks";

import { QueryErrorBoundary } from "@/components/QueryErrorBoundary";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import {
  Item,
  ItemContent,
  ItemTitle,
  ItemDescription,
  ItemGroup,
  ItemSeparator,
} from "@/components/ui/item";
import { Notice } from "@/components/Notice";
import { GameDetailAppBar } from "./AppBar";
import { Panel } from "../../components/Panel";
import {
  ChannelMessage,
  useGameRetrieveSuspense,
  useGamesChannelsListSuspense,
} from "@/api/generated/endpoints";

const getLatestMessagePreview = (
  messages: readonly ChannelMessage[]
): string => {
  if (messages.length === 0) return "No messages";
  const latestMessage = messages[messages.length - 1];
  return `${latestMessage.sender.nation.name}: ${latestMessage.body}`;
};

const ChannelListScreen: React.FC = () => {
  const { gameId, phaseId } = useRequiredParams<{
    gameId: string;
    phaseId: string;
  }>();
  const { data: game } = useGameRetrieveSuspense(gameId);
  const { data: channels } = useGamesChannelsListSuspense(gameId);

  const isSandboxGame = game.sandbox;

  return (
    <div className="flex flex-col flex-1">
      <GameDetailAppBar title="Chat" />
      <div className="flex-1 overflow-y-auto">
        <Panel>
          <Panel.Content>
            {isSandboxGame ? (
              <Notice
                icon={MessageSquare}
                title="Chat is not available in sandbox games."
                className="h-full"
              />
            ) : channels.length === 0 ? (
              <Notice
                icon={MessageSquare}
                title="No channels created"
                className="h-full"
              />
            ) : (
              <ItemGroup>
                {channels.map(channel => (
                  <React.Fragment key={channel.id}>
                    <Item asChild size="sm">
                      <Link
                        to={`/game/${gameId}/phase/${phaseId}/chat/channel/${channel.id}`}
                        className="text-foreground no-underline"
                      >
                        <ItemContent>
                          <ItemTitle>
                            {channel.name}
                            {!channel.private && (
                              <Badge variant="outline">Public</Badge>
                            )}
                          </ItemTitle>
                          <ItemDescription>
                            {getLatestMessagePreview(channel.messages)}
                          </ItemDescription>
                        </ItemContent>
                      </Link>
                    </Item>
                    <ItemSeparator />
                  </React.Fragment>
                ))}
              </ItemGroup>
            )}
          </Panel.Content>
          {!isSandboxGame && (
            <>
              <Separator />
              <Panel.Footer>
                <div className="flex justify-end w-full">
                  <Button asChild>
                    <Link to={`/game/${gameId}/phase/${phaseId}/chat/channel/create`}>
                      <UserPlus className="size-4" />
                      Create Channel
                    </Link>
                  </Button>
                </div>
              </Panel.Footer>
            </>
          )}
        </Panel>
      </div>
    </div>
  );
};

const ChannelListScreenSuspense: React.FC = () => (
  <QueryErrorBoundary>
    <Suspense fallback={<div></div>}>
      <ChannelListScreen />
    </Suspense>
  </QueryErrorBoundary>
);

export { ChannelListScreenSuspense as ChannelListScreen };
