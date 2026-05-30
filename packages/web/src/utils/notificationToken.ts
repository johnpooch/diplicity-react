import {
  requestPermission,
  getToken as getNativeToken,
} from "@/messaging-native";
import { getToken as getWebToken, registerServiceWorker } from "@/messaging";
import { isNativePlatform, isIosPlatform } from "@/utils/platform";

type NotificationToken = {
  token: string;
  type: "ios" | "android" | "web";
};

const requestNotificationPermission =
  async (): Promise<NotificationToken | null> => {
    if (isNativePlatform()) {
      const result = await requestPermission();
      if (result !== "granted") return null;
      const token = await getNativeToken();
      return token ? { token, type: isIosPlatform() ? "ios" : "android" } : null;
    }

    if (!("Notification" in window)) return null;
    if (Notification.permission === "denied") return null;

    const permission =
      Notification.permission === "granted"
        ? "granted"
        : await Notification.requestPermission();

    if (permission !== "granted") return null;

    await registerServiceWorker();
    try {
      const token = await getWebToken();
      return token ? { token, type: "web" } : null;
    } catch {
      return null;
    }
  };

export { requestNotificationPermission };
export type { NotificationToken };
