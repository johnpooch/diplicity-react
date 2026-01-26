import { lazy } from "react";

export const GameDetail = {
  MapScreen: lazy(() =>
    import("./MapScreen").then((m) => ({ default: m.MapScreen }))
  ),
  OrdersScreen: lazy(() =>
    import("./OrdersScreen").then((m) => ({ default: m.OrdersScreen }))
  ),
  ChannelListScreen: lazy(() =>
    import("./ChannelListScreen").then((m) => ({ default: m.ChannelListScreen }))
  ),
  ChannelCreateScreen: lazy(() =>
    import("./ChannelCreateScreen").then((m) => ({
      default: m.ChannelCreateScreen,
    }))
  ),
  ChannelScreen: lazy(() =>
    import("./ChannelScreen").then((m) => ({ default: m.ChannelScreen }))
  ),
  GameInfoScreen: lazy(() =>
    import("./GameInfoScreen").then((m) => ({ default: m.GameInfoScreen }))
  ),
  PlayerInfoScreen: lazy(() =>
    import("./PlayerInfoScreen").then((m) => ({ default: m.PlayerInfoScreen }))
  ),
};
