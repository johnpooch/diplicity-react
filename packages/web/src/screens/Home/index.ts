import { lazy } from "react";

export const Home = {
  MyGames: lazy(() => import("./MyGames").then((m) => ({ default: m.MyGames }))),
  FindGames: lazy(() =>
    import("./FindGames").then((m) => ({ default: m.FindGames }))
  ),
  CreateGame: lazy(() =>
    import("./CreateGame").then((m) => ({ default: m.CreateGame }))
  ),
  Profile: lazy(() => import("./Profile").then((m) => ({ default: m.Profile }))),
  GameInfoScreen: lazy(() =>
    import("./GameInfo").then((m) => ({ default: m.GameInfoScreen }))
  ),
  PlayerInfoScreen: lazy(() =>
    import("./PlayerInfo").then((m) => ({ default: m.PlayerInfoScreen }))
  ),
  SandboxGames: lazy(() =>
    import("./SandboxGames").then((m) => ({ default: m.SandboxGames }))
  ),
};
