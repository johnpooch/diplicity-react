import { createContext, useContext, useEffect, useState } from "react";
import { onMessageReceived, getToken } from "../messaging";
import { selectAuth, service } from "../store";
import { useSelector } from "react-redux";

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
  const { loggedIn } = useSelector(selectAuth);
  const [token, setToken] = useState<string | undefined>(undefined);
  const [error, setError] = useState<string | null>(null);
  const [isCheckingToken, setIsCheckingToken] = useState(true);
  const devicesListQuery = service.endpoints.devicesList.useQuery(undefined, {
    skip: !loggedIn,
  });
  const [createDevice] = service.endpoints.devicesCreate.useMutation();

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
    onMessageReceived((_payload) => {
      // Handle received message
    });
  }, []);

  useEffect(() => {
    const createDeviceFromToken = async (token: string) => {
      await createDevice({
        fcmDevice: {
          type: "web",
          registrationId: token,
          active: true,
        },
      }).unwrap();
      setToken(token);
    };
    if (token && loggedIn) {
      createDeviceFromToken(token);
    }
  }, [token, loggedIn]);

  useEffect(() => {
    const checkInitialState = async () => {
      // If permission is already granted, get the token silently
      // This allows NotificationBanner to show correctly
      if (Notification.permission === "granted") {
        await tryGetToken();
      }
      setIsCheckingToken(false);
    };
    checkInitialState();
  }, []);

  const enableMessaging = async (): Promise<void> => {
    try {
      setError(null);

      // Check current permission state
      const currentPermission = Notification.permission;

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
        await createDevice({
          fcmDevice: {
            registrationId: token,
            type: "web",
            active: false,
          },
        }).unwrap();
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

  const permissionDenied = Notification.permission === "denied";

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

export { MessagingContextProvider, useMessaging };
