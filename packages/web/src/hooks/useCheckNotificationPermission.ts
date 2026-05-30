import { useCallback } from "react";
import { toast } from "sonner";
import { useDevicesCreate, getDevicesListQueryKey } from "@/api/generated/endpoints";
import { useQueryClient } from "@tanstack/react-query";
import { checkPermission } from "@/messaging-native";
import { isNativePlatform } from "@/utils/platform";
import { requestNotificationPermission } from "@/utils/notificationToken";

const DENIED_MESSAGE =
  "No notification permission.\nTo be informed of games and messages, allow notifications in your settings.";

const useCheckNotificationPermission = () => {
  const createDeviceMutation = useDevicesCreate();
  const queryClient = useQueryClient();

  return useCallback(async () => {
    if (isNativePlatform()) {
      const permission = await checkPermission();
      if (permission === "denied") { toast.warning(DENIED_MESSAGE); return; }
      if (permission !== "prompt") return;
    } else {
      if (!("Notification" in window)) return;
      if (Notification.permission === "denied") { toast.warning(DENIED_MESSAGE); return; }
      if (Notification.permission !== "default") return;
    }

    const result = await requestNotificationPermission();
    if (!result) { toast.warning(DENIED_MESSAGE); return; }

    await createDeviceMutation.mutateAsync({
      data: { type: result.type, registrationId: result.token, active: true },
    });
    queryClient.invalidateQueries({ queryKey: getDevicesListQueryKey() });
    // eslint-disable-next-line react-hooks/exhaustive-deps -- mutateAsync is stable
  }, []);
};

export { useCheckNotificationPermission };
