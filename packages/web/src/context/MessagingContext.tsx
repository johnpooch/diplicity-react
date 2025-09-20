import { createContext, useContext, useEffect, useState } from "react";
import { onMessageReceived, getToken } from "../messaging";
import { selectAuth, service } from "../store";
import { useSelector } from "react-redux";

type MessagingContextType = {
  enabled: boolean;
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
    tryGetToken();
  }, []);

  const enableMessaging = async (): Promise<void> => {
    try {
      const permission = await Notification.requestPermission();
      if (permission === "granted") {
        await tryGetToken();
      } else {
        console.warn("Notification permission not granted");
      }
    } catch (error) {
      console.error("An error occurred while requesting permission. ", error);
    }
  };

  const disableMessaging = async (): Promise<void> => {
    try {
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

  return (
    <MessagingContext.Provider
      value={{ enabled, disableMessaging, enableMessaging }}
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
