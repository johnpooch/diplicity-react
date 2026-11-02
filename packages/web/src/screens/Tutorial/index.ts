import { lazyScreen } from "../../utils/lazyScreen";

export const Tutorial = {
  TutorialScreen: lazyScreen(
    () => import("./TutorialScreen"),
    "TutorialScreen"
  ),
};
