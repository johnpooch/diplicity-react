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
    onMessageReceived((payload) => {
      console.log("Message received. ", payload);
    });
  }, []);

  useEffect(() => {
    const createDeviceFromToken = async (token: string) => {
      console.log("Creating device with token:", token);
      await createDevice({
        fcmDevice: {
          type: "web",
          registrationId: token,
          active: true,
        },
      }).unwrap();
      console.log("Device created with token:", token);
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
    console.log("Disabling messaging");
    try {
      if (token) {
        console.log("Deleting token");
        await createDevice({
          fcmDevice: {
            registrationId: token,
            type: "web",
            active: false,
          },
        }).unwrap();
        console.log("Token deleted");
        setToken(undefined);
      }
    } catch (error) {
      console.error("An error occurred while deleting token. ", error);
    }
  };

  console.log("Devices list query data:", devicesListQuery.data);

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
