import type { Decorator } from "@storybook/react";
import { HomeLayout } from "../components/HomeLayout";
import { GameDetailLayout } from "../components/GameDetailLayout";

export const withHomeLayout: Decorator = Story => (
  <HomeLayout>
    <Story />
  </HomeLayout>
);

export const withGameDetailLayout: Decorator = Story => (
  <GameDetailLayout>
    <Story />
  </GameDetailLayout>
);
