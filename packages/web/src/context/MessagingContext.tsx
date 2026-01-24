import { createContext, useContext, useEffect, useState } from "react";
import { onMessageReceived, getToken, registerServiceWorker } from "../messaging";
import { useAuth } from "../auth";
import { useDevicesList, useDevicesCreate } from "../api/generated/endpoints";

type MessagingContextType = {
  enabled: boolean;
  permissionDenied: boolean;
  error: string | null;
  isLoading: boolean;
  disableMessaging: () => Promise<void>;
  enableMessaging: () => Promise<void>;
};

const MessagingContext = createContext<MessagingContextType | undefined>(
  undefined
);

type MessagingContextProviderProps = React.PropsWithChildren<
  Record<string, unknown>
>;

const MessagingContextProvider: React.FC<MessagingContextProviderProps> = (
  props
) => {
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
      const token = await getToken();
      if (token) {
        setToken(token);
      }
    } catch (error) {
      console.error("An error occurred while retrieving token. ", error);
    }
  };

  useEffect(() => {
    onMessageReceived(() => {
      // Handle received message
    });
  }, []);

  useEffect(() => {
    const createDeviceFromToken = async (token: string) => {
      await createDeviceMutation.mutateAsync({
        data: {
          type: "web",
          registrationId: token,
          active: true,
        },
      });
      setToken(token);
    };
    if (token && loggedIn) {
      createDeviceFromToken(token);
    }
  }, [token, loggedIn, createDeviceMutation]);

  useEffect(() => {
    // Register the service worker for Firebase messaging
    registerServiceWorker();

    // Check if Notification is supported by the browser - some browsers don't support it (e.g. Safari)
    if (isNotificationSupported) {
      const checkInitialState = async () => {
        // If permission is already granted, get the token silently
        // This allows NotificationBanner to show correctly
        if (Notification.permission === "granted") {
          await tryGetToken();
        }
        setIsCheckingToken(false);
      };
      checkInitialState();
    } else {
      // On unsupported browsers, immediately mark as not checking
      setIsCheckingToken(false);
    }
  }, [isNotificationSupported]);

  const enableMessaging = async (): Promise<void> => {
    try {
      setError(null);

      // Check current permission state
      const currentPermission = isNotificationSupported ? Notification.permission : "granted";

      if (currentPermission === "denied") {
        setError("Notifications are blocked. Please enable them in your browser settings.");
        return;
      }

      // Request permission if not already granted
      const permission = currentPermission === "granted"
        ? "granted"
        : await Notification.requestPermission();

      if (permission === "granted") {
        await tryGetToken();
      } else if (permission === "denied") {
        setError("Notification permission was denied. Please enable it in your browser settings.");
      } else {
        setError("Notification permission was not granted.");
      }
    } catch (error) {
      console.error("An error occurred while requesting permission. ", error);
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
    } catch (error) {
      console.error("An error occurred while deleting token. ", error);
      setError("Failed to disable notifications. Please try again.");
    }
  };

  // Notifications are considered "enabled" if the token is set and the devices
  // is in the list and active
  const enabled = Boolean(
    token !== undefined &&
    devicesListQuery.data?.some(
      (device) => device.registrationId === token && device.active
    )
  );

  const permissionDenied = isNotificationSupported ? Notification.permission === "denied" : false;

  // Still loading if checking token OR devices list is loading (when logged in)
  const isLoading = isCheckingToken || (loggedIn && devicesListQuery.isLoading);

  return (
    <MessagingContext.Provider
      value={{ enabled, permissionDenied, error, isLoading, disableMessaging, enableMessaging }}
    >
      {props.children}
    </MessagingContext.Provider>
  );
};

const useMessaging = () => {
  const messaging = useContext(MessagingContext);
  if (!messaging) {
    throw new Error("useMessaging must be used within a MessagingProvider");
  }
  return messaging;
};

export { MessagingContext, MessagingContextProvider, useMessaging };
