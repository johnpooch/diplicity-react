import { useEffect, useRef, useState } from "react";
import {
  onMessageReceived,
  getToken as getWebToken,
  registerServiceWorker,
} from "../messaging";
import {
  checkPermission,
  requestPermission,
  getToken as getNativeToken,
  addTokenRefreshListener,
  addNotificationReceivedListener,
} from "../messaging-native";
import { useQueryClient } from "@tanstack/react-query";
import { useAuth } from "../auth";
import {
  getDevicesListQueryKey,
  useDevicesList,
  useDevicesCreate,
} from "../api/generated/endpoints";
import { isNativePlatform, isIosPlatform } from "../utils/platform";

type MessagingState = {
  enabled: boolean;
  permissionDenied: boolean;
  error: string | null;
  disableMessaging: () => Promise<void>;
  enableMessaging: () => Promise<void>;
};

const getNativeDeviceType = (): "ios" | "android" =>
  isIosPlatform() ? "ios" : "android";

const useMessaging = (): MessagingState => {
  const { loggedIn } = useAuth();
  const [error, setError] = useState<string | null>(null);
  const [nativePermissionDenied, setNativePermissionDenied] = useState(false);
  const devicesListQuery = useDevicesList({
    query: { enabled: loggedIn },
  });
  const createDeviceMutation = useDevicesCreate();
  const queryClient = useQueryClient();

  const native = isNativePlatform();
  const deviceType = native ? getNativeDeviceType() : "web";

  const devicesRef = useRef(devicesListQuery.data);
  devicesRef.current = devicesListQuery.data;

  // Check native permission state on mount for the denied indicator
  useEffect(() => {
    if (!native) return;
    checkPermission().then(permission => {
      if (permission === "denied") setNativePermissionDenied(true);
    });
  }, [native]);

  // Token refresh listener (native only) — re-register if notifications are active
  useEffect(() => {
    if (!native) return;
    const listener = addTokenRefreshListener(async (newToken) => {
      const activeDevice = devicesRef.current?.find(
        d => d.active && d.type === getNativeDeviceType()
      );
      if (activeDevice) {
        await createDeviceMutation.mutateAsync({
          data: { type: getNativeDeviceType(), registrationId: newToken, active: true },
        });
        queryClient.invalidateQueries({ queryKey: getDevicesListQueryKey() });
      }
    });
    return () => {
      listener.then(l => l.remove());
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps -- mutateAsync is stable
  }, [native]);

  // Foreground message handler
  useEffect(() => {
    if (native) {
      const listener = addNotificationReceivedListener(() => {
        queryClient.invalidateQueries();
      });
      return () => {
        listener.then(l => l.remove());
      };
    } else {
      return onMessageReceived(() => {
        queryClient.invalidateQueries();
      });
    }
  }, [native, queryClient]);

  const enableMessaging = async (): Promise<void> => {
    try {
      setError(null);
      let token: string | null = null;

      if (native) {
        const result = await requestPermission();
        if (result !== "granted") {
          setNativePermissionDenied(true);
          setError(
            "Notification permission was denied. Please enable it in Settings > Diplicity > Notifications."
          );
          return;
        }
        setNativePermissionDenied(false);
        token = await getNativeToken();
      } else {
        if (!("Notification" in window)) return;

        if (Notification.permission === "denied") {
          setError(
            "Notifications are blocked. Please enable them in your browser settings."
          );
          return;
        }

        const permission =
          Notification.permission === "granted"
            ? "granted"
            : await Notification.requestPermission();

        if (permission !== "granted") {
          setError(
            permission === "denied"
              ? "Notification permission was denied. Please enable it in your browser settings."
              : "Notification permission was not granted."
          );
          return;
        }

        registerServiceWorker();
        try {
          token = await getWebToken();
        } catch (err) {
          console.error("An error occurred while retrieving token.", err);
        }
      }

      if (token) {
        await createDeviceMutation.mutateAsync({
          data: { type: deviceType, registrationId: token, active: true },
        });
        queryClient.invalidateQueries({ queryKey: getDevicesListQueryKey() });
      }
    } catch {
      setError("Failed to enable notifications. Please try again.");
    }
  };

  const disableMessaging = async (): Promise<void> => {
    try {
      setError(null);
      const activeDevice = devicesListQuery.data?.find(
        d => d.active && d.type === deviceType
      );
      if (activeDevice) {
        await createDeviceMutation.mutateAsync({
          data: { registrationId: activeDevice.registrationId, type: deviceType, active: false },
        });
        queryClient.invalidateQueries({ queryKey: getDevicesListQueryKey() });
      }
    } catch {
      setError("Failed to disable notifications. Please try again.");
    }
  };

  const enabled = Boolean(
    devicesListQuery.data?.some(d => d.active && d.type === deviceType)
  );

  const permissionDenied = native
    ? nativePermissionDenied
    : "Notification" in window && Notification.permission === "denied";

  return { enabled, permissionDenied, error, disableMessaging, enableMessaging };
};

export { useMessaging };
export type { MessagingState };
