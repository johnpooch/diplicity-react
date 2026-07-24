import { useMemo } from "react";
import { useLocation, useSearchParams } from "react-router";
import { Map, Gavel, MessageCircle, Info, Users, type LucideIcon } from "lucide-react";
import { useRequiredParams } from "@/hooks/useRequiredParams";
import { useGameRetrieve } from "@/api/generated/endpoints";

export interface GameNavItem {
  label: string;
  icon: LucideIcon;
  path: string;
  isActive: boolean;
  badge?: string;
}

const navigationItems = [
  { label: "Map", icon: Map, path: "/game/:gameId/phase/:phaseId" },
  { label: "Orders", icon: Gavel, path: "/game/:gameId/phase/:phaseId/orders" },
  { label: "Chat", icon: MessageCircle, path: "/game/:gameId/phase/:phaseId/chat" },
  { label: "Game Info", icon: Info, path: "/game/:gameId/phase/:phaseId/game-info" },
  { label: "Player Info", icon: Users, path: "/game/:gameId/phase/:phaseId/player-info" },
];

const useGameNavItems = (): GameNavItem[] => {
  const location = useLocation();
  const [searchParams] = useSearchParams();
  const { gameId, phaseId } = useRequiredParams<{
    gameId: string;
    phaseId: string;
  }>();

  const { data: game } = useGameRetrieve(gameId, {
    query: {
      refetchInterval: query =>
        query.state.data?.status === "active" ? 5000 : false,
    },
  });

  return useMemo(() => {
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
};

export { useGameNavItems };
