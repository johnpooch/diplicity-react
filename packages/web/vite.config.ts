import { defineConfig as defineTestConfig } from "vitest/config";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";
import { copyFileSync } from "fs";
import { resolve } from "path";

// https://vite.dev/config/
const config = defineConfig({
  plugins: [
    react(),
    {
      name: 'copy-staticwebapp-config',
      writeBundle() {
        // Copy staticwebapp.config.json to dist directory
        copyFileSync(
          resolve(__dirname, 'staticwebapp.config.json'),
          resolve(__dirname, 'dist', 'staticwebapp.config.json')
        );
      }
    }
  ],
  server: {
    watch: {
      usePolling: true,
      interval: 1000,
    },
    host: true,
    strictPort: true,
  }
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
