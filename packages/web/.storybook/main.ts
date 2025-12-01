import type { StorybookConfig } from "@storybook/react-vite";
import { mergeConfig } from "vite";
import { resolve } from "path";

const config: StorybookConfig = {
  stories: ["../src/**/*.stories.@(js|jsx|mjs|ts|tsx)"],
  addons: [
    "@storybook/addon-onboarding",
    "@storybook/addon-essentials",
    "@chromatic-com/storybook",
    "@storybook/addon-interactions",
  ],
  framework: {
    name: "@storybook/react-vite",
    options: {},
  },
  viteFinal: async config => {
    const { default: tailwindcss } = await import("@tailwindcss/vite");
    return mergeConfig(config, {
      plugins: [tailwindcss()],
      resolve: {
        alias: {
          "@": resolve(__dirname, "../src"),
        },
      },
    });
  },
};
export default config;
