import { lazyScreen } from "../../utils/lazyScreen";

export const Home = {
  MyGames: lazyScreen(() => import("./MyGames"), "MyGames"),
  FindGames: lazyScreen(() => import("./FindGames"), "FindGames"),
  CreateGame: lazyScreen(() => import("./CreateGame"), "CreateGame"),
  Account: lazyScreen(() => import("./Account"), "Account"),
  GameInfoScreen: lazyScreen(() => import("./GameInfo"), "GameInfoScreen"),
  PlayerInfoScreen: lazyScreen(() => import("./PlayerInfo"), "PlayerInfoScreen"),
  NationPreferenceScreen: lazyScreen(
    () => import("./NationPreference"),
    "NationPreferenceScreen"
  ),
  NationAssignmentScreen: lazyScreen(
    () => import("./NationAssignment"),
    "NationAssignmentScreen"
  ),
  Community: lazyScreen(() => import("./Community"), "Community"),
  DeleteAccount: lazyScreen(() => import("./DeleteAccount"), "DeleteAccount"),
  LearnToPlay: lazyScreen(() => import("./LearnToPlay"), "LearnToPlay"),
  PlayerProfileScreen: lazyScreen(
    () => import("./PlayerProfile"),
    "PlayerProfileScreen"
  ),
};
