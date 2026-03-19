import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./tests",
  testMatch: "screenshots.spec.ts",
  fullyParallel: false,
  retries: 0,
  workers: 1,
  reporter: "list",
  use: {
    baseURL: "http://localhost:5173",
  },
  projects: [
    {
      name: "iphone-6.5",
      use: {
        browserName: "chromium",
        viewport: { width: 428, height: 926 },
        deviceScaleFactor: 3,
      },
    },
    {
      name: "ipad-13",
      use: {
        browserName: "chromium",
        viewport: { width: 1024, height: 1366 },
        deviceScaleFactor: 2,
      },
    },
  ],
});
