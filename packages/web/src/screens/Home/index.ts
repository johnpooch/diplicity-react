import { lazy } from "react";

export const Home = {
  MyGames: lazy(() => import("./MyGames").then((m) => ({ default: m.MyGames }))),
  FindGames: lazy(() =>
    import("./FindGames").then((m) => ({ default: m.FindGames }))
  ),
  OpenGames: lazy(() =>
    import("./OpenGames").then((m) => ({ default: m.OpenGames }))
  ),
  CreateGame: lazy(() =>
    import("./CreateGame").then((m) => ({ default: m.CreateGame }))
  ),
  Account: lazy(() =>
    import("./Account").then((m) => ({ default: m.Account }))
  ),
  GameInfoScreen: lazy(() =>
    import("./GameInfo").then((m) => ({ default: m.GameInfoScreen }))
  ),
  PlayerInfoScreen: lazy(() =>
    import("./PlayerInfo").then((m) => ({ default: m.PlayerInfoScreen }))
  ),
  Community: lazy(() =>
    import("./Community").then((m) => ({ default: m.Community }))
  ),
  DeleteAccount: lazy(() =>
    import("./DeleteAccount").then((m) => ({ default: m.DeleteAccount }))
  ),
  LearnToPlay: lazy(() =>
    import("./LearnToPlay").then((m) => ({ default: m.LearnToPlay }))
  ),
  PlayerProfileScreen: lazy(() =>
    import("./PlayerProfile").then((m) => ({
      default: m.PlayerProfileScreen,
    }))
  ),
};
