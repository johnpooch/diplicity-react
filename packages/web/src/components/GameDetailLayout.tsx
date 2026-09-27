import React, { useEffect, useMemo, useRef, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import {
  Link,
  Navigate,
  useLocation,
  useNavigate,
  useParams,
  useSearchParams,
} from "react-router";
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
import { PendingGameMapPreview } from "@/components/PendingGameMapPreview";
import { SafeAreaView } from "@/components/SafeAreaView";
import { OfflineBanner } from "@/components/OfflineBanner";
import { getGameLandingPath } from "@/util";
import { useIsMobile } from "@/hooks/use-mobile";
import {
  useGameRetrieve,
  getGameOptionsRetrieveQueryKey,
  getGameOrdersListQueryKey,
  getGamePhaseRetrieveQueryKey,
  getGamePhasesListQueryKey,
  getGamePhaseStatesListQueryKey,
} from "@/api/generated/endpoints";

const navigationItems = [
  { label: "Map", icon: Map, path: "", pendingVisible: false },
  { label: "Orders", icon: Gavel, path: "/orders", pendingVisible: false },
  { label: "Chat", icon: MessageCircle, path: "/chat", pendingVisible: false },
  { label: "Players", icon: Users, path: "/player-info", pendingVisible: true },
  { label: "Info", icon: Info, path: "/game-info", pendingVisible: true },
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
  const isMobile = useIsMobile();
  const { gameId } = useRequiredParams<{ gameId: string }>();
  const { phaseId } = useParams<{ phaseId: string }>();
  const [isPanelCollapsed, setIsPanelCollapsed] = useState(false);

  const { data: game } = useGameRetrieve(gameId, {
    query: {
      refetchInterval: (query) => {
        const status = query.state.data?.status;
        return status === "active" ? 5000 : status === "pending" ? 10000 : false;
      },
    },
  });

  const queryClient = useQueryClient();
  const currentPhaseId = game?.currentPhaseId;
  const status = game?.status;
  const observedGameRef = useRef<{
    gameId: string;
    currentPhaseId: number | null;
    status: string;
  } | null>(null);

  useEffect(() => {
    if (currentPhaseId === undefined || status === undefined) return;
    const previous = observedGameRef.current;
    observedGameRef.current = { gameId, currentPhaseId, status };
    if (
      !previous ||
      previous.gameId !== gameId ||
      (previous.currentPhaseId === currentPhaseId && previous.status === status)
    ) {
      return;
    }
    const affectedPhaseIds = [
      ...new Set([previous.currentPhaseId, currentPhaseId]),
    ].filter((id): id is number => id !== null);

    const queryKeys = [
      getGamePhaseStatesListQueryKey(gameId),
      getGameOptionsRetrieveQueryKey(gameId),
      getGamePhasesListQueryKey(gameId),
      ...affectedPhaseIds.flatMap(id => [
        getGamePhaseRetrieveQueryKey(gameId, id),
        getGameOrdersListQueryKey(gameId, id),
      ]),
    ];

    void Promise.all(
      queryKeys.map(queryKey => queryClient.invalidateQueries({ queryKey }))
    );
  }, [gameId, currentPhaseId, status, queryClient]);

  const [searchParams] = useSearchParams();

  const shellBasePath = phaseId
    ? `/game/${gameId}/phase/${phaseId}`
    : `/game/${gameId}`;

  const navItems = useMemo(() => {
    const visibleItems = navigationItems.filter(
      item => (phaseId || item.pendingVisible) && (!game?.sandbox || item.label !== "Chat")
    );
    const searchParamsStr = searchParams.toString();
    const chatBasePath = `${shellBasePath}/chat`;
    const isInChatChannel = location.pathname.startsWith(chatBasePath + "/");
    return visibleItems.map(item => {
      const basePath = `${shellBasePath}${item.path}`;
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
  }, [shellBasePath, phaseId, searchParams, location.pathname, game?.totalUnreadMessageCount, game?.sandbox, game?.members]);

  // Filter out Map for desktop sidebar since map is already visible in right
  // panel. Unlike the bottom nav, the sidebar Chat icon should return to the
  // channel list rather than resuming the last channel, since the map is
  // always visible alongside the chat in the desktop layout.
  const sidebarNavItems = useMemo(() => {
    const params = new URLSearchParams(searchParams);
    params.delete("channelId");
    const paramsStr = params.toString();
    const chatBasePath = `${shellBasePath}/chat`;
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
  }, [navItems, searchParams, shellBasePath]);

  const bottomClasses = cn("border-t bg-background", "block md:hidden");

  // The backend pre-creates a game's first phase before it starts, so
  // currentPhaseId is already non-null while pending — status (not
  // currentPhaseId nullness) is what flips when the game starts. Declarative
  // (like GamePhaseRedirect/GameReplaceRedirect) rather than an effect
  // calling navigate(), so it can't miss a transition observed elsewhere.
  if (!phaseId && game && status !== "pending" && currentPhaseId) {
    const leaf = location.pathname.slice(`/game/${gameId}`.length);
    const target =
      leaf === "/game-info" || leaf === "/player-info"
        ? `/game/${gameId}/phase/${currentPhaseId}${leaf}`
        : getGameLandingPath(game, isMobile);
    return <Navigate to={target} replace />;
  }

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
                onItemClick={path => {
                  const item = sidebarNavItems.find(i => i.path === path);
                  if (item?.isActive && !isPanelCollapsed) {
                    setIsPanelCollapsed(true);
                  } else {
                    setIsPanelCollapsed(false);
                    navigate(path);
                  }
                }}
                className="w-full p-0"
              />
            </SidebarContent>
            <SidebarFooter className="p-0">
              <div className="size-8" aria-hidden />
            </SidebarFooter>
          </Sidebar>

          {/* Main Content Area - Fixed width on desktop */}
          <SidebarInset
            className={cn(
              "@container flex min-w-0 min-h-0 flex-col bg-sidebar",
              isPanelCollapsed ? "md:hidden" : "md:w-[400px] md:flex-none"
            )}
          >
            {children}
          </SidebarInset>

          {/* Right Panel - GameMap (desktop only) */}
          <div className="hidden md:flex flex-1 border-l overflow-hidden bg-muted">
            {phaseId ? (
              <GameMap />
            ) : (
              game && <PendingGameMapPreview game={game} />
            )}
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
