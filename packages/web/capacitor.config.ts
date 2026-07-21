import type { CapacitorConfig } from "@capacitor/cli";

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
  },
};

export default config;
