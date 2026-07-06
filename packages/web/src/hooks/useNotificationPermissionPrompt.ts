import { useEffect, useRef } from "react";
import { useInfiniteQuery, useQueryClient } from "@tanstack/react-query";
import { useAuth } from "@/auth";
import {
  useDevicesList,
  useDevicesCreate,
  getDevicesListQueryKey,
} from "@/api/generated/endpoints";
import { checkPermission } from "@/messaging-native";
import { isNativePlatform, isIosPlatform } from "@/utils/platform";
import { requestNotificationPermission } from "@/utils/notificationToken";
import { useCheckNotificationPermission } from "./useCheckNotificationPermission";
import { gamesListInfiniteQueryOptions } from "./useGamesListInfinite";

const useNotificationPermissionPrompt = () => {
  const { loggedIn } = useAuth();
  const hasPromptedRef = useRef(false);
  const checkNotificationPermission = useCheckNotificationPermission();
  const createDeviceMutation = useDevicesCreate();
  const queryClient = useQueryClient();

  const { data: activeGamesData } = useInfiniteQuery({
    ...gamesListInfiniteQueryOptions({
      mine: true,
      status: "active",
      ordering: "deadline",
    }),
    enabled: loggedIn,
  });

  const hasActiveNonSandboxGame =
    activeGamesData?.pages.some(page =>
      page.results.some(game => !game.sandbox)
    ) ?? false;

  const { data: devicesData, isLoading: devicesLoading } = useDevicesList({
    query: { enabled: loggedIn },
  });

  // Prompt for permission when user has active games and hasn't been asked yet
  useEffect(() => {
    if (!loggedIn || hasPromptedRef.current) return;
    if (!hasActiveNonSandboxGame) return;

    hasPromptedRef.current = true;
    checkNotificationPermission();
  }, [loggedIn, hasActiveNonSandboxGame, checkNotificationPermission]);

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
