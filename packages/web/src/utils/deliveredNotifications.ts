import { clearDeliveredNotifications as clearNativeDeliveredNotifications } from "@/messaging-native";
import { clearDeliveredNotifications as clearWebDeliveredNotifications } from "@/messaging";
import { isNativePlatform } from "@/utils/platform";

const clearDeliveredNotifications = async (): Promise<void> => {
  try {
    if (isNativePlatform()) {
      await clearNativeDeliveredNotifications();
    } else {
      await clearWebDeliveredNotifications();
    }
  } catch (error) {
    console.error("Failed to clear delivered notifications:", error);
  }
};

export { clearDeliveredNotifications };
