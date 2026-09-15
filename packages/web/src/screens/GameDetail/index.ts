import { lazyScreen } from "../../utils/lazyScreen";

export const GameDetail = {
  MapScreen: lazyScreen(() => import("./MapScreen"), "MapScreen"),
  OrdersScreen: lazyScreen(() => import("./OrdersScreen"), "OrdersScreen"),
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
  VariantDetailsScreen: lazyScreen(
    () => import("./VariantDetailsScreen"),
    "VariantDetailsScreen"
  ),
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
  ReplaceScreen: lazyScreen(() => import("./ReplaceScreen"), "ReplaceScreen"),
};
