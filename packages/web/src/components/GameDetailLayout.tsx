import React, { useMemo } from "react";
import { Link, useLocation, useNavigate, useSearchParams } from "react-router";
import { useRequiredParams } from "@/hooks";
import { Map, Gavel, MessageCircle, Users, Info } from "lucide-react";
import { cn } from "@/lib/utils";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
  SidebarInset,
  SidebarProvider,
} from "@/components/ui/sidebar";
import { DiplicityLogo } from "@/components/DiplicityLogo";
import { Navigation } from "@/components/Navigation";
import { GameMap } from "@/components/GameMap";
import { SafeAreaView } from "@/components/SafeAreaView";
import { OfflineBanner } from "@/components/OfflineBanner";
import { useGameRetrieve } from "@/api/generated/endpoints";

const navigationItems = [
  { label: "Map", icon: Map, path: "/game/:gameId/phase/:phaseId" },
  { label: "Orders", icon: Gavel, path: "/game/:gameId/phase/:phaseId/orders" },
  { label: "Chat", icon: MessageCircle, path: "/game/:gameId/phase/:phaseId/chat" },
  { label: "Players", icon: Users, path: "/game/:gameId/phase/:phaseId/player-info" },
  { label: "Info", icon: Info, path: "/game/:gameId/phase/:phaseId/game-info" },
];

interface GameDetailLayoutProps {
  children: React.ReactNode;
  className?: string;
}

const GameDetailLayout: React.FC<GameDetailLayoutProps> = ({
  children,
  className,
}) => {
  const navigate = useNavigate();
  const location = useLocation();
  const { gameId, phaseId } = useRequiredParams<{
    gameId: string;
    phaseId: string;
  }>();

  const { data: game } = useGameRetrieve(gameId, {
    query: {
      refetchInterval: (query) =>
        query.state.data?.status === "active" ? 5000 : false,
    },
  });

  const [searchParams] = useSearchParams();

  const navItems = useMemo(() => {
    const items = game?.sandbox
      ? navigationItems.filter(item => item.label !== "Chat")
      : navigationItems;
    const searchParamsStr = searchParams.toString();
    const chatBasePath = `/game/${gameId}/phase/${phaseId}/chat`;
    const isInChatChannel = location.pathname.startsWith(chatBasePath + "/");
    return items.map(item => {
      const basePath = item.path
        .replace(":gameId", gameId)
        .replace(":phaseId", phaseId);
      const badge =
        (item.label === "Chat" &&
          game?.totalUnreadMessageCount &&
          game.totalUnreadMessageCount > 0) ||
        (item.label === "Orders" &&
          Array.isArray(game?.members) &&
          game.members.some(m => m.isCurrentUser && m.civilDisorder))
          ? "•"
          : undefined;
      let path: string;
      if (item.label === "Chat" && isInChatChannel) {
        const params = new URLSearchParams(searchParams);
        params.delete("channelId");
        const paramsStr = params.toString();
        path = paramsStr ? `${chatBasePath}?${paramsStr}` : chatBasePath;
      } else {
        path = searchParamsStr ? `${basePath}?${searchParamsStr}` : basePath;
      }
      const isActive = item.label === "Chat"
        ? location.pathname === chatBasePath || location.pathname.startsWith(chatBasePath + "/")
        : location.pathname === basePath;
      return {
        ...item,
        path,
        isActive,
        badge,
      };
    });
  }, [gameId, phaseId, searchParams, location.pathname, game?.totalUnreadMessageCount, game?.sandbox, game?.members]);

  // Filter out Map for desktop sidebar since map is already visible in right
  // panel. Unlike the bottom nav, the sidebar Chat icon should return to the
  // channel list rather than resuming the last channel, since the map is
  // always visible alongside the chat in the desktop layout.
  const sidebarNavItems = useMemo(() => {
    const params = new URLSearchParams(searchParams);
    params.delete("channelId");
    const paramsStr = params.toString();
    const chatBasePath = `/game/${gameId}/phase/${phaseId}/chat`;
    return navItems
      .filter(item => item.label !== "Map")
      .map(item =>
        item.label === "Chat"
          ? {
              ...item,
              path: paramsStr ? `${chatBasePath}?${paramsStr}` : chatBasePath,
            }
          : item
      );
  }, [navItems, searchParams, gameId, phaseId]);

  const bottomClasses = cn("border-t bg-background", "block md:hidden");

  return (
    <SidebarProvider>
      <SafeAreaView
        className={cn(
          "flex flex-col h-dvh w-full overflow-hidden",
          className
        )}
      >
        <OfflineBanner />
        <div className="flex items-stretch flex-1 min-h-0 w-full">
          {/* Left Sidebar - Icons only */}
          <Sidebar collapsible="none" className="hidden w-[72px] px-3 py-6 md:flex">
            <SidebarHeader className="p-0">
              <Link to="/" aria-label="Home" className="flex w-full justify-center">
                <DiplicityLogo />
              </Link>
            </SidebarHeader>
            <SidebarContent className="justify-center">
              <Navigation
                items={sidebarNavItems}
                variant="compact"
                onItemClick={path => navigate(path)}
                className="w-full p-0"
              />
            </SidebarContent>
            <SidebarFooter className="p-0">
              <div className="size-8" aria-hidden />
            </SidebarFooter>
          </Sidebar>

          {/* Main Content Area - Fixed width on desktop */}
          <SidebarInset className="@container flex min-w-0 min-h-0 flex-col md:w-[360px] md:flex-none">
            {children}
          </SidebarInset>

          {/* Right Panel - GameMap (desktop only) */}
          <div className="hidden md:flex flex-1 border-l overflow-hidden">
            <GameMap />
          </div>
        </div>

        {/* Bottom Navigation - Mobile only */}
        <div className={bottomClasses}>
          <Navigation
            items={navItems}
            variant="bottom"
            onItemClick={path => navigate(path)}
          />
        </div>
      </SafeAreaView>
    </SidebarProvider>
  );
};

export { GameDetailLayout };
export type { GameDetailLayoutProps };
