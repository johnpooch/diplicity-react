import React, { useMemo } from "react";
import { useLocation, useNavigate } from "react-router";
import { useRequiredParams } from "@/hooks";
import { ArrowLeft, Map, Gavel, MessageCircle } from "lucide-react";
import { cn } from "@/lib/utils";
import {
  Sidebar,
  SidebarContent,
  SidebarHeader,
  SidebarInset,
  SidebarProvider,
} from "@/components/ui/sidebar";
import { Button } from "@/components/ui/button";
import { Navigation } from "@/components/Navigation";
import { GameMap } from "@/components/GameMap";
import { SafeAreaView } from "@/components/SafeAreaView";
import { useGameRetrieve } from "@/api/generated/endpoints";

const navigationItems = [
  { label: "Map", icon: Map, path: "/game/:gameId/phase/:phaseId" },
  { label: "Orders", icon: Gavel, path: "/game/:gameId/phase/:phaseId/orders" },
  { label: "Chat", icon: MessageCircle, path: "/game/:gameId/phase/:phaseId/chat" },
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
    query: { refetchInterval: 30000 },
  });

  const navItems = useMemo(() => {
    const items = game?.sandbox
      ? navigationItems.filter(item => item.label !== "Chat")
      : navigationItems;
    return items.map(item => {
      const path = item.path
        .replace(":gameId", gameId)
        .replace(":phaseId", phaseId);
      const badge =
        item.label === "Chat" &&
        game?.totalUnreadMessageCount &&
        game.totalUnreadMessageCount > 0
          ? "•"
          : undefined;
      return {
        ...item,
        path,
        isActive: location.pathname === path,
        badge,
      };
    });
  }, [gameId, phaseId, location.pathname, game?.totalUnreadMessageCount, game?.sandbox]);

  // Filter out Map for desktop sidebar since map is already visible in right panel
  const sidebarNavItems = useMemo(
    () => navItems.filter(item => item.label !== "Map"),
    [navItems]
  );

  const bottomClasses = cn("border-t bg-background", "block md:hidden");

  return (
    <SidebarProvider>
      <SafeAreaView
        className={cn(
          "flex flex-col h-dvh w-full overflow-hidden",
          className
        )}
      >
        <div className="flex items-stretch flex-1 min-h-0 w-full">
          {/* Left Sidebar - Icons only */}
          <Sidebar collapsible="none" className="hidden md:flex w-14">
            <SidebarHeader className="p-2">
              <Button
                variant="ghost"
                size="icon"
                onClick={() => navigate("/")}
                aria-label="Back to home"
              >
                <ArrowLeft className="size-4" />
              </Button>
            </SidebarHeader>
            <SidebarContent>
              <Navigation
                items={sidebarNavItems}
                variant="compact"
                onItemClick={path => navigate(path)}
              />
            </SidebarContent>
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
