import { lazy } from "react";

export const Tutorial = {
  TutorialScreen: lazy(() =>
    import("./TutorialScreen").then(m => ({ default: m.TutorialScreen }))
  ),
};
