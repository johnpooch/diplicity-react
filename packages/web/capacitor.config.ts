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
  plugins: {
    SplashScreen: {
      launchAutoHide: true,
      launchShowDuration: 2000,
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
  },
};

export default config;
