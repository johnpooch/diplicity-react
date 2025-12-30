import { IconName } from "../components/Icon";

export interface NavigationItemData {
  label: string;
  icon: IconName;
  path: string;
}

export const homeNavigationItems: NavigationItemData[] = [
  { label: "My Games", icon: IconName.MyGames, path: "/" },
  { label: "Find Games", icon: IconName.FindGames, path: "/find-games" },
  { label: "Create Game", icon: IconName.CreateGame, path: "/create-game" },
  { label: "Sandbox", icon: IconName.Sandbox, path: "/sandbox" },
  { label: "Profile", icon: IconName.Profile, path: "/profile" },
];

export const gameDetailNavigationItems: NavigationItemData[] = [
  { label: "Map", icon: IconName.Map, path: "/game/:gameId" },
  { label: "Orders", icon: IconName.Orders, path: "/game/:gameId/orders" },
  { label: "Chat", icon: IconName.Chat, path: "/game/:gameId/chat" },
];
