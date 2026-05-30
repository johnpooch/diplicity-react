import { useCallback } from "react";
import { toast } from "sonner";
import { useDevicesCreate } from "@/api/generated/endpoints";
import {
  checkPermission,
  requestPermission,
  getToken as getNativeToken,
} from "@/messaging-native";
import { getToken as getWebToken, registerServiceWorker } from "@/messaging";
import { isNativePlatform, isIosPlatform } from "@/utils/platform";

const getDeviceType = (): "ios" | "android" =>
  isIosPlatform() ? "ios" : "android";

const DENIED_MESSAGE =
  "No notification permission.\nTo be informed of games and messages, allow notifications in your settings.";

const useCheckNotificationPermission = () => {
  const createDeviceMutation = useDevicesCreate();

  return useCallback(async () => {
    if (isNativePlatform()) {
      const permission = await checkPermission();

      if (permission === "denied") {
        toast.warning(DENIED_MESSAGE);
        return;
      }

      if (permission === "prompt") {
        const result = await requestPermission();
        if (result === "granted") {
          const token = await getNativeToken();
          if (token) {
            await createDeviceMutation.mutateAsync({
              data: { type: getDeviceType(), registrationId: token, active: true },
            });
          }
        } else {
          toast.warning(DENIED_MESSAGE);
        }
      }
    } else {
      if (!("Notification" in window)) return;

      if (Notification.permission === "denied") {
        toast.warning(DENIED_MESSAGE);
        return;
      }

      if (Notification.permission === "default") {
        registerServiceWorker();
        const result = await Notification.requestPermission();
        if (result === "granted") {
          const token = await getWebToken();
          if (token) {
            await createDeviceMutation.mutateAsync({
              data: { type: "web", registrationId: token, active: true },
            });
          }
        } else {
          toast.warning(DENIED_MESSAGE);
        }
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- mutateAsync is stable
  }, []);
};

export { useCheckNotificationPermission };
