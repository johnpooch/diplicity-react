import { useEffect, useRef } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { useAuth } from "@/auth";
import {
  useGamesList,
  useDevicesList,
  useDevicesCreate,
  getDevicesListQueryKey,
} from "@/api/generated/endpoints";
import { checkPermission } from "@/messaging-native";
import { isNativePlatform, isIosPlatform } from "@/utils/platform";
import { requestNotificationPermission } from "@/utils/notificationToken";
import { useCheckNotificationPermission } from "./useCheckNotificationPermission";

const useNotificationPermissionPrompt = () => {
  const { loggedIn } = useAuth();
  const hasPromptedRef = useRef(false);
  const checkNotificationPermission = useCheckNotificationPermission();
  const createDeviceMutation = useDevicesCreate();
  const queryClient = useQueryClient();

  const { data: activeGamesData } = useGamesList(
    { mine: true, status: "active", sandbox: false },
    { query: { enabled: loggedIn } }
  );

  const { data: devicesData, isLoading: devicesLoading } = useDevicesList({
    query: { enabled: loggedIn },
  });

  // Prompt for permission when user has active games and hasn't been asked yet
  useEffect(() => {
    if (!loggedIn || hasPromptedRef.current) return;
    if (activeGamesData === undefined) return;
    if (activeGamesData.count === 0) return;

    hasPromptedRef.current = true;
    checkNotificationPermission();
  }, [loggedIn, activeGamesData, checkNotificationPermission]);

  // Silently re-register if permission is already granted but device record is missing
  useEffect(() => {
    if (!loggedIn || devicesLoading || devicesData === undefined) return;

    const deviceType = isNativePlatform()
      ? isIosPlatform() ? "ios" : "android"
      : "web";

    if (devicesData.some(d => d.active && d.type === deviceType)) return;

    const reRegister = async () => {
      if (isNativePlatform()) {
        const permission = await checkPermission();
        if (permission !== "granted") return;
      } else {
        if (!("Notification" in window) || Notification.permission !== "granted") return;
      }

      const result = await requestNotificationPermission();
      if (!result) return;

      await createDeviceMutation.mutateAsync({
        data: { type: result.type, registrationId: result.token, active: true },
      });
      queryClient.invalidateQueries({ queryKey: getDevicesListQueryKey() });
    };

    reRegister();
    // eslint-disable-next-line react-hooks/exhaustive-deps -- mutateAsync is stable
  }, [loggedIn, devicesLoading, devicesData]);
};

export { useNotificationPermissionPrompt };
