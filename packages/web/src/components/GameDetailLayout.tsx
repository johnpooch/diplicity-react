import React, { useMemo } from "react";
import { useNavigate, useSearchParams } from "react-router";
import { useGameNavItems, useRequiredParams } from "@/hooks";
import { ArrowLeft } from "lucide-react";
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

interface GameDetailLayoutProps {
  children: React.ReactNode;
  className?: string;
}

const GameDetailLayout: React.FC<GameDetailLayoutProps> = ({
  children,
  className,
}) => {
  const navigate = useNavigate();
  const { gameId, phaseId } = useRequiredParams<{
    gameId: string;
    phaseId: string;
  }>();

  const [searchParams] = useSearchParams();
  const navItems = useGameNavItems();

  // Unlike the bottom nav, the sidebar Chat icon should return to the
  // channel list rather than resuming the last channel, since the map is
  // always visible alongside the chat in the desktop layout.
  const sidebarNavItems = useMemo(() => {
    const params = new URLSearchParams(searchParams);
    params.delete("channelId");
    const paramsStr = params.toString();
    const chatBasePath = `/game/${gameId}/phase/${phaseId}/chat`;
    return navItems.map(item =>
      item.label === "Chat"
        ? {
            ...item,
            path: paramsStr ? `${chatBasePath}?${paramsStr}` : chatBasePath,
          }
        : item
    );
  }, [navItems, searchParams, gameId, phaseId]);

  // Selecting Map on desktop hides the content column so GameMap fills the
  // rest of the screen next to the icon sidebar.
  const isMapFocused =
    navItems.find(item => item.label === "Map")?.isActive ?? false;

  return (
    <SidebarProvider>
      <SafeAreaView
        className={cn(
          "flex flex-col h-dvh w-full overflow-hidden",
          className
        )}
      >
        <div className="flex items-stretch flex-1 min-h-0 w-full">
          {/* Left Sidebar - Icons only (desktop) */}
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
          <SidebarInset
            className={cn(
              "@container flex min-w-0 min-h-0 flex-col md:flex-none",
              isMapFocused ? "md:hidden md:w-0" : "md:w-[360px]"
            )}
          >
            {children}
          </SidebarInset>

          {/* Right Panel - GameMap (desktop only) */}
          <div className="hidden md:flex flex-1 border-l overflow-hidden">
            <GameMap />
          </div>
        </div>

        {/* Bottom Navigation - Mobile only */}
        <div className="md:hidden border-t bg-background">
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
