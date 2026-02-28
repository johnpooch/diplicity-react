import { useEffect, useState } from "react";
import {
  onMessageReceived,
  getToken as getWebToken,
  registerServiceWorker,
} from "../messaging";
import {
  checkPermission,
  requestPermission,
  getToken as getIosToken,
  addTokenRefreshListener,
  addNotificationReceivedListener,
} from "../messaging-ios";
import { useQueryClient } from "@tanstack/react-query";
import { useAuth } from "../auth";
import {
  getDevicesListQueryKey,
  useDevicesList,
  useDevicesCreate,
} from "../api/generated/endpoints";
import { isNativePlatform } from "../utils/platform";

type MessagingState = {
  enabled: boolean;
  permissionDenied: boolean;
  error: string | null;
  isLoading: boolean;
  disableMessaging: () => Promise<void>;
  enableMessaging: () => Promise<void>;
};

const useMessaging = (): MessagingState => {
  const { loggedIn } = useAuth();
  const [token, setToken] = useState<string | undefined>(undefined);
  const [error, setError] = useState<string | null>(null);
  const [isCheckingToken, setIsCheckingToken] = useState(true);
  const [nativePermissionDenied, setNativePermissionDenied] = useState(false);
  const devicesListQuery = useDevicesList({
    query: { enabled: loggedIn },
  });
  const createDeviceMutation = useDevicesCreate();
  const queryClient = useQueryClient();

  const native = isNativePlatform();

  // Effect 1: Initialization (platform-branched)
  useEffect(() => {
    if (native) {
      const initIos = async () => {
        const permission = await checkPermission();
        if (permission === "granted") {
          const t = await getIosToken();
          if (t) setToken(t);
        }
        if (permission === "denied") {
          setNativePermissionDenied(true);
        }
        setIsCheckingToken(false);
      };
      initIos();
    } else {
      registerServiceWorker();

      const isNotificationSupported = "Notification" in window;
      if (isNotificationSupported) {
        const checkInitialState = async () => {
          if (Notification.permission === "granted") {
            try {
              const t = await getWebToken();
              if (t) setToken(t);
            } catch (err) {
              console.error(
                "An error occurred while retrieving token. ",
                err
              );
            }
          }
          setIsCheckingToken(false);
        };
        checkInitialState();
      } else {
        setIsCheckingToken(false);
      }
    }
  }, [native]);

  // Effect 2: Token registration (shared, type-aware)
  useEffect(() => {
    const createDeviceFromToken = async (t: string) => {
      await createDeviceMutation.mutateAsync({
        data: {
          type: native ? "ios" : "web",
          registrationId: t,
          active: true,
        },
      });
      queryClient.invalidateQueries({ queryKey: getDevicesListQueryKey() });
    };
    if (token && loggedIn) {
      createDeviceFromToken(token);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- mutateAsync is stable, including the mutation object causes infinite loops
  }, [token, loggedIn]);

  // Effect 3: Token refresh listener (iOS only)
  useEffect(() => {
    if (!native) return;
    const listener = addTokenRefreshListener((newToken) => {
      setToken(newToken);
    });
    return () => {
      listener.then((l) => l.remove());
    };
  }, [native]);

  // Effect 4: Foreground message handler (platform-branched)
  useEffect(() => {
    if (native) {
      const listener = addNotificationReceivedListener(() => {
        queryClient.invalidateQueries();
      });
      return () => {
        listener.then((l) => l.remove());
      };
    } else {
      onMessageReceived(() => {
        queryClient.invalidateQueries();
      });
    }
  }, [native, queryClient]);

  const enableMessaging = async (): Promise<void> => {
    try {
      setError(null);

      if (native) {
        const result = await requestPermission();
        if (result === "granted") {
          const t = await getIosToken();
          if (t) setToken(t);
          setNativePermissionDenied(false);
        } else {
          setNativePermissionDenied(true);
          setError(
            "Notification permission was denied. Please enable it in Settings > Diplicity > Notifications."
          );
        }
      } else {
        const isNotificationSupported = "Notification" in window;
        const currentPermission = isNotificationSupported
          ? Notification.permission
          : "granted";

        if (currentPermission === "denied") {
          setError(
            "Notifications are blocked. Please enable them in your browser settings."
          );
          return;
        }

        const permission =
          currentPermission === "granted"
            ? "granted"
            : await Notification.requestPermission();

        if (permission === "granted") {
          try {
            const t = await getWebToken();
            if (t) setToken(t);
          } catch (err) {
            console.error(
              "An error occurred while retrieving token. ",
              err
            );
          }
        } else if (permission === "denied") {
          setError(
            "Notification permission was denied. Please enable it in your browser settings."
          );
        } else {
          setError("Notification permission was not granted.");
        }
      }
    } catch (err) {
      console.error("An error occurred while requesting permission. ", err);
      setError("Failed to enable notifications. Please try again.");
    }
  };

  const disableMessaging = async (): Promise<void> => {
    try {
      setError(null);
      if (token) {
        await createDeviceMutation.mutateAsync({
          data: {
            registrationId: token,
            type: native ? "ios" : "web",
            active: false,
          },
        });
        queryClient.invalidateQueries({ queryKey: getDevicesListQueryKey() });
        setToken(undefined);
      }
    } catch (err) {
      console.error("An error occurred while deleting token. ", err);
      setError("Failed to disable notifications. Please try again.");
    }
  };

  const deviceType = native ? "ios" : "web";
  const enabled = Boolean(
    token !== undefined &&
      devicesListQuery.data?.some(
        (device) =>
          device.registrationId === token &&
          device.active &&
          device.type === deviceType
      )
  );

  const permissionDenied = native
    ? nativePermissionDenied
    : "Notification" in window && Notification.permission === "denied";

  const isLoading =
    isCheckingToken || (loggedIn && devicesListQuery.isLoading);

  return {
    enabled,
    permissionDenied,
    error,
    isLoading,
    disableMessaging,
    enableMessaging,
  };
};

export { useMessaging };
export type { MessagingState };
