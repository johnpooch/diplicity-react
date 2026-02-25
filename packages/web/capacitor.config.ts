import type { CapacitorConfig } from "@capacitor/cli";

const config: CapacitorConfig = {
  appId: "com.diplicity.app",
  appName: "Diplicity",
  webDir: "dist",
  ios: {
    webContentsDebuggingEnabled: true,
  },
  server: {
    iosScheme: "capacitor",
  },
};

export default config;
