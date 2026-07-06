import { lazyScreen } from "../../utils/lazyScreen";

export const Home = {
  MyGames: lazyScreen(() => import("./MyGames"), "MyGames"),
  FindGames: lazyScreen(() => import("./FindGames"), "FindGames"),
  CreateGame: lazyScreen(() => import("./CreateGame"), "CreateGame"),
  Account: lazyScreen(() => import("./Account"), "Account"),
  PlayerInfoScreen: lazyScreen(() => import("./PlayerInfo"), "PlayerInfoScreen"),
  Community: lazyScreen(() => import("./Community"), "Community"),
  DeleteAccount: lazyScreen(() => import("./DeleteAccount"), "DeleteAccount"),
  LearnToPlay: lazyScreen(() => import("./LearnToPlay"), "LearnToPlay"),
  PlayerProfileScreen: lazyScreen(
    () => import("./PlayerProfile"),
    "PlayerProfileScreen"
  ),
};
