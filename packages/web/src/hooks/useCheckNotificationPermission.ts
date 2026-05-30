import { useCallback } from "react";
import { toast } from "sonner";
import { useDevicesCreate } from "@/api/generated/endpoints";
import {
  checkPermission,
  requestPermission,
  getToken,
} from "@/messaging-native";
import { isNativePlatform, isIosPlatform } from "@/utils/platform";

const getDeviceType = (): "ios" | "android" =>
  isIosPlatform() ? "ios" : "android";

const useCheckNotificationPermission = () => {
  const createDeviceMutation = useDevicesCreate();

  return useCallback(async () => {
    if (!isNativePlatform()) return;

    const permission = await checkPermission();

    if (permission === "denied") {
      toast.warning(
        "No Android notification permission\nTo be informed of games and messages, allow notifications in Settings > Notifications > App notifications."
      );
      return;
    }

    if (permission === "prompt") {
      const result = await requestPermission();
      if (result === "granted") {
        const token = await getToken();
        if (token) {
          await createDeviceMutation.mutateAsync({
            data: { type: getDeviceType(), registrationId: token, active: true },
          });
        }
      } else {
        toast.warning(
          "No Android notification permission\nTo be informed of games and messages, allow notifications in Settings > Notifications > App notifications."
        );
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- mutateAsync is stable
  }, []);
};

export { useCheckNotificationPermission };
