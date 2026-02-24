import { useEffect, useState } from "react";
import {
  onMessageReceived,
  getToken,
  registerServiceWorker,
} from "../messaging";
import { useAuth } from "../auth";
import { useDevicesList, useDevicesCreate } from "../api/generated/endpoints";

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
  const devicesListQuery = useDevicesList({
    query: { enabled: loggedIn },
  });
  const createDeviceMutation = useDevicesCreate();

  const isNotificationSupported = "Notification" in window;

  const tryGetToken = async () => {
    try {
      const t = await getToken();
      if (t) {
        setToken(t);
      }
    } catch (err) {
      console.error("An error occurred while retrieving token. ", err);
    }
  };

  useEffect(() => {
    onMessageReceived(() => {
      // Handle received message
    });
  }, []);

  useEffect(() => {
    const createDeviceFromToken = async (t: string) => {
      await createDeviceMutation.mutateAsync({
        data: {
          type: "web",
          registrationId: t,
          active: true,
        },
      });
      setToken(t);
    };
    if (token && loggedIn) {
      createDeviceFromToken(token);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- mutateAsync is stable, including the mutation object causes infinite loops
  }, [token, loggedIn]);

  useEffect(() => {
    registerServiceWorker();

    if (isNotificationSupported) {
      const checkInitialState = async () => {
        if (Notification.permission === "granted") {
          await tryGetToken();
        }
        setIsCheckingToken(false);
      };
      checkInitialState();
    } else {
      setIsCheckingToken(false);
    }
  }, [isNotificationSupported]);

  const enableMessaging = async (): Promise<void> => {
    try {
      setError(null);

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
        await tryGetToken();
      } else if (permission === "denied") {
        setError(
          "Notification permission was denied. Please enable it in your browser settings."
        );
      } else {
        setError("Notification permission was not granted.");
      }
    } catch (err) {
      console.error(
        "An error occurred while requesting permission. ",
        err
      );
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
            type: "web",
            active: false,
          },
        });
        setToken(undefined);
      }
    } catch (err) {
      console.error("An error occurred while deleting token. ", err);
      setError("Failed to disable notifications. Please try again.");
    }
  };

  const enabled = Boolean(
    token !== undefined &&
      devicesListQuery.data?.some(
        (device) => device.registrationId === token && device.active
      )
  );

  const permissionDenied = isNotificationSupported
    ? Notification.permission === "denied"
    : false;

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
