import { lazyScreen } from "../../utils/lazyScreen";

export const GameDetail = {
  MapScreen: lazyScreen(() => import("./MapScreen"), "MapScreen"),
  OrdersScreen: lazyScreen(() => import("./OrdersScreen"), "OrdersScreen"),
  OverviewScreen: lazyScreen(
    () => import("./OverviewScreen"),
    "OverviewScreen"
  ),
  ChannelListScreen: lazyScreen(
    () => import("./ChannelListScreen"),
    "ChannelListScreen"
  ),
  ChannelCreateScreen: lazyScreen(
    () => import("./ChannelCreateScreen"),
    "ChannelCreateScreen"
  ),
  ChannelScreen: lazyScreen(() => import("./ChannelScreen"), "ChannelScreen"),
  GameInfoScreen: lazyScreen(() => import("./GameInfoScreen"), "GameInfoScreen"),
  PlayerInfoScreen: lazyScreen(
    () => import("./PlayerInfoScreen"),
    "PlayerInfoScreen"
  ),
  ProposeDrawScreen: lazyScreen(
    () => import("./ProposeDrawScreen"),
    "ProposeDrawScreen"
  ),
  DrawProposalsScreen: lazyScreen(
    () => import("./DrawProposalsScreen"),
    "DrawProposalsScreen"
  ),
  PlayerProfileScreen: lazyScreen(
    () => import("./PlayerProfileScreen"),
    "PlayerProfileScreen"
  ),
};
