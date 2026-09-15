import type { CapacitorConfig } from "@capacitor/cli";

const apiBaseUrl =
  process.env.VITE_DIPLICITY_API_BASE_URL || "http://localhost:8000";

const config: CapacitorConfig = {
  appId: "com.diplicity.app",
  appName: "Diplicity",
  webDir: "dist",
  backgroundColor: "#291b1b",
  ios: {
    webContentsDebuggingEnabled: true,
  },
  android: {
    webContentsDebuggingEnabled: true,
  },
  server: {
    iosScheme: "capacitor",
  },
  plugins: {
    SplashScreen: {
      launchAutoHide: false,
      launchFadeOutDuration: 500,
      backgroundColor: "#291b1b",
      showSpinner: false,
    },
    SocialLogin: {
      providers: {
        google: true,
        apple: true,
      },
    },
    FirebaseMessaging: {
      presentationOptions: ["badge", "sound", "alert"],
    },
    CapacitorUpdater: {
      autoUpdate: "atBackground",
      updateUrl: `${apiBaseUrl.replace(/\/$/, "")}/update/check/`,
      statsUrl: "",
      channelUrl: "",
    },
  },
};

export default config;
