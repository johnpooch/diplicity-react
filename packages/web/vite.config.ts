import { defineConfig as defineTestConfig } from "vitest/config";
import { defineConfig, type PluginOption } from "vite";
import react from "@vitejs/plugin-react-swc";
import { copyFileSync } from "fs";
import { resolve } from "path";
import tailwindcss from "@tailwindcss/vite";
import { visualizer } from "rollup-plugin-visualizer";

// https://vite.dev/config/
const config = defineConfig({
  plugins: [
    react(),
    tailwindcss(),
    {
      name: "copy-staticwebapp-config",
      writeBundle() {
        // Copy staticwebapp.config.json to dist directory
        copyFileSync(
          resolve(__dirname, "staticwebapp.config.json"),
          resolve(__dirname, "dist", "staticwebapp.config.json")
        );
      },
    },
    process.env.ANALYZE &&
      visualizer({
        open: true,
        filename: "stats.html",
        gzipSize: true,
        brotliSize: true,
      }),
  ].filter(Boolean) as PluginOption[],
  resolve: {
    alias: {
      "@": resolve(__dirname, "src"),
    },
  },
  server: {
    watch: {
      usePolling: true,
      interval: 1000,
    },
    host: true,
    strictPort: true,
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          "vendor-react": ["react", "react-dom", "react-router"],
          "vendor-ui": [
            "@radix-ui/react-accordion",
            "@radix-ui/react-avatar",
            "@radix-ui/react-checkbox",
            "@radix-ui/react-dialog",
            "@radix-ui/react-dropdown-menu",
            "@radix-ui/react-hover-card",
            "@radix-ui/react-label",
            "@radix-ui/react-scroll-area",
            "@radix-ui/react-select",
            "@radix-ui/react-separator",
            "@radix-ui/react-slot",
            "@radix-ui/react-switch",
            "@radix-ui/react-tabs",
            "@radix-ui/react-tooltip",
            "lucide-react",
          ],
          "vendor-query": ["@tanstack/react-query"],
          "vendor-observability": [
            "@sentry/react",
            "@opentelemetry/api",
            "@opentelemetry/sdk-trace-web",
            "@opentelemetry/exporter-trace-otlp-http",
            "@opentelemetry/instrumentation",
            "@opentelemetry/instrumentation-document-load",
            "@opentelemetry/instrumentation-fetch",
            "@opentelemetry/instrumentation-xml-http-request",
            "@opentelemetry/resources",
            "@opentelemetry/context-zone",
            "@opentelemetry/semantic-conventions",
          ],
          "vendor-firebase": ["firebase/app", "firebase/messaging"],
        },
      },
    },
  },
});

const testConfig = defineTestConfig({
  test: {
    globals: true,
    environment: "jsdom",
    setupFiles: "./vitest.setup.ts",
    exclude: ["e2e/**", "node_modules/**"],
  },
});

export default {
  ...config,
  ...testConfig,
};
