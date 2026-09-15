import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { ListItem, ListSection } from "@/components/ui/list";
import { ScreenContainer } from "@/components/ui/screen-container";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { GameDetailShell } from "@/components/GameDetailShell";
import { NationFlag, NationFlagsProvider } from "@/components/NationFlag";
import { activeChannelList, pendingChannelList } from "@/data/fixtures";
import type { ChannelPreview } from "@/data/types";
import { Megaphone, Plus } from "lucide-react";

interface ScreenConfig {
  channels: ChannelPreview[];
  showCreate: boolean;
  hideFlags?: boolean;
}

const screens: Record<string, ScreenConfig> = {
  active: {
    channels: activeChannelList,
    showCreate: true,
  },
  "active-no-flags": {
    channels: activeChannelList,
    showCreate: true,
    hideFlags: true,
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
    return <NationFlag nation={nations[0]} size="lg" />;
  }

  return (
    <div className="flex size-12 shrink-0 items-center justify-center">
      <div className="flex -space-x-3">
        {nations.slice(0, 3).map(nation => (
          <NationFlag
            key={nation}
            nation={nation}
            size="md"
            className="ring-2 ring-card"
          />
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

const ChannelRow: React.FC<{ channel: ChannelPreview }> = ({ channel }) => {
  return (
    <ListItem
      href={channelPath(channel.id)}
      leading={<ChannelMedia nations={channel.nations} />}
      title={channel.name}
      subtitle={preview(channel)}
      trailing={
        channel.unread ? (
          <span
            className="size-2 shrink-0 rounded-full bg-primary"
            aria-label="Unread"
          />
        ) : undefined
      }
    />
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
    <NationFlagsProvider enabled={!screen.hideFlags}>
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
        <ListSection>
          {screen.channels.map(channel => (
            <ChannelRow key={channel.id} channel={channel} />
          ))}
        </ListSection>
        {screen.showCreate && (
          <Button className="w-full" size="lg" asChild>
            <Link to={createChannelPath}>Create Channel</Link>
          </Button>
        )}
      </ScreenContainer>
    </GameDetailShell>
    </NationFlagsProvider>
  );
};

export { ChatChannelList };
