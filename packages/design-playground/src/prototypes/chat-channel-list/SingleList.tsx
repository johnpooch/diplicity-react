import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { ScreenContainer } from "@/components/ui/screen-container";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { GameDetailShell } from "@/components/GameDetailShell";
import { NationFlag } from "@/components/NationFlag";
import { activeChannelList, pendingChannelList } from "@/data/fixtures";
import type { ChannelPreview } from "@/data/types";
import { Megaphone, Plus } from "lucide-react";

interface ScreenConfig {
  channels: ChannelPreview[];
  showCreate: boolean;
}

const screens: Record<string, ScreenConfig> = {
  active: {
    channels: activeChannelList,
    showCreate: true,
  },
  pending: {
    channels: pendingChannelList,
    showCreate: false,
  },
};

const createChannelPath = "/create-channel/single-form";

const channelPath = (id: string) => {
  if (id === "france") {
    return "/chat-channel/nation-bubbles/direct";
  }

  return "/chat-channel/nation-bubbles/group";
};

const ChannelMedia: React.FC<{ nations: string[] }> = ({ nations }) => {
  if (nations.length === 0) {
    return (
      <div className="flex size-12 shrink-0 items-center justify-center rounded-full border bg-muted">
        <Megaphone className="size-5 text-muted-foreground" />
      </div>
    );
  }

  if (nations.length === 1) {
    return (
      <div className="size-12 shrink-0 overflow-hidden rounded-full border">
        <NationFlag nation={nations[0]} />
      </div>
    );
  }

  return (
    <div className="flex size-12 shrink-0 items-center justify-center">
      <div className="flex -space-x-3">
        {nations.slice(0, 3).map(nation => (
          <div
            key={nation}
            className="size-8 overflow-hidden rounded-full border-2 border-card"
          >
            <NationFlag nation={nation} />
          </div>
        ))}
      </div>
    </div>
  );
};

const preview = (channel: ChannelPreview) => {
  if (!channel.lastSender || !channel.lastBody) {
    return "No messages";
  }

  return `${channel.lastSender}: ${channel.lastBody}`;
};

const ChannelCard: React.FC<{ channel: ChannelPreview }> = ({ channel }) => {
  return (
    <Link to={channelPath(channel.id)} className="block">
      <Card className="overflow-hidden py-0 transition-colors hover:bg-accent/50">
        <CardContent className="flex items-center gap-3 p-3">
          <ChannelMedia nations={channel.nations} />
          <div className="flex min-w-0 flex-1 flex-col gap-0.5">
            <p className="flex min-w-0 items-center gap-2 leading-tight">
              <span className="truncate font-semibold">{channel.name}</span>
              {channel.unread && (
                <span
                  className="size-2 shrink-0 rounded-full bg-primary"
                  aria-label="Unread"
                />
              )}
            </p>
            <p className="truncate text-sm text-muted-foreground">
              {preview(channel)}
            </p>
          </div>
        </CardContent>
      </Card>
    </Link>
  );
};

const HeaderActions: React.FC<{
  size: "icon" | "icon-sm";
  withTooltip: boolean;
}> = ({ size, withTooltip }) => {
  const button = (
    <Button size={size} variant="outline" aria-label="Create channel" asChild>
      <Link to={createChannelPath}>
        <Plus />
      </Link>
    </Button>
  );

  if (!withTooltip) {
    return button;
  }

  return (
    <Tooltip>
      <TooltipTrigger asChild>{button}</TooltipTrigger>
      <TooltipContent>Create channel</TooltipContent>
    </Tooltip>
  );
};

const ChatChannelList: React.FC<{ state: string }> = ({ state }) => {
  const screen = screens[state] ?? screens.active;
  const headerAction = screen.showCreate ? (
    <HeaderActions size="icon-sm" withTooltip={false} />
  ) : undefined;

  return (
    <GameDetailShell
      title="Chats"
      activeNavItem="Chat"
      headerAction={headerAction}
      chatUnread={screen.channels.some(channel => channel.unread)}
    >
      <ScreenContainer>
        <div className="hidden h-9 items-center justify-between gap-2 md:flex">
          <h1 className="min-w-0 truncate text-xl font-semibold leading-9">
            Chats
          </h1>
          {screen.showCreate && <HeaderActions size="icon" withTooltip />}
        </div>
        <div className="flex flex-col gap-2">
          {screen.channels.map(channel => (
            <ChannelCard key={channel.id} channel={channel} />
          ))}
        </div>
        {screen.showCreate && (
          <Button className="w-full" size="lg" asChild>
            <Link to={createChannelPath}>Create Channel</Link>
          </Button>
        )}
      </ScreenContainer>
    </GameDetailShell>
  );
};

export { ChatChannelList };
