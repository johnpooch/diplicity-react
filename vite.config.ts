import { defineConfig as defineTestConfig } from "vitest/config";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";

// https://vite.dev/config/
const config = defineConfig({
  plugins: react(),
});

const testConfig = defineTestConfig({
  test: {
    globals: true,
    environment: "jsdom",
    setupFiles: "./vitest.setup.ts",
  },
});

export default {
  ...config,
  ...testConfig
}
