import { lazyScreen } from "../../utils/lazyScreen";

export const Moderation = {
  ModerationQueue: lazyScreen(
    () => import("./ModerationQueue"),
    "ModerationQueue"
  ),
  ModerationReport: lazyScreen(
    () => import("./ModerationReport"),
    "ModerationReport"
  ),
};
