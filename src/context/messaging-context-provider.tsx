import { createContext, useContext, useEffect, useState } from "react";
import { initializeApp } from "firebase/app";
import {
  getToken,
  deleteToken,
  onMessage,
  getMessaging,
} from "firebase/messaging";
import { useFcmTokenReceivedMutation } from "../common";

const firebaseConfig = {
  apiKey: "AIzaSyCsbBMuoeynbqGJ0WqKKd5hkXK4QyQtY-0",
  authDomain: "diplicity-engine.firebaseapp.com",
  databaseURL: "https://diplicity-engine.firebaseio.com",
  projectId: "diplicity-engine",
  storageBucket: "diplicity-engine.firebasestorage.app",
  messagingSenderId: "635122585664",
  appId: "1:635122585664:web:2a5a7f0a72c9647fa74fa5",
  measurementId: "G-SFEBT2PQ6W",
};

const app = initializeApp(firebaseConfig);
const messaging = getMessaging(app);

const VAPID_KEY =
  "BNP8q-LcJTZa_zweDRrLnhfInysDihizGh9RiE9_lzAxPXYrG6UFrwG9lcMnPlKopUFRUwx6JwF9R30had-5lnI";

type MessagingContextType = {
  enabled: boolean;
  disableMessaging: () => Promise<void>;
  enableMessaging: () => Promise<void>;
  token?: string;
};

const MessagingContext = createContext<MessagingContextType | undefined>(
  undefined
);

type MessagingContextProviderProps = React.PropsWithChildren<
  Record<string, unknown>
>;

const ENABLED = true;
const DISABLED = false;

const MessagingContextProvider: React.FC<MessagingContextProviderProps> = (
  props
) => {
  const [handleFcmTokenReceived, mutation] = useFcmTokenReceivedMutation();
  const [token, setToken] = useState<string | undefined>(undefined);
  const enabled = token !== undefined;

  const retrieveToken = async (): Promise<string | null> => {
    try {
      const currentToken = await getToken(messaging, { vapidKey: VAPID_KEY });
      if (currentToken) {
        setToken(currentToken);
        console.log("Token available");
        // Here you would send token to server
        return currentToken;
      } else {
        console.warn(
          "No registration token available. Request permission to generate one."
        );
        return null;
      }
    } catch (error) {
      console.error("An error occurred while retrieving token. ", error);
      return null;
    }
  };

  useEffect(() => {
    retrieveToken();

    const unsubscribe = onMessage(messaging, (payload) => {
      console.log("Message received. ", payload);
    });

    return () => {
      unsubscribe();
    };
  }, []);

  const enableMessaging = async (): Promise<void> => {
    try {
      const permission = await Notification.requestPermission();
      if (permission === "granted") {
        const token = await retrieveToken();
        if (token) {
          console.log("Token available and permission granted");
          await handleFcmTokenReceived(token, ENABLED);
        }
      } else {
        console.warn("Notification permission not granted");
      }
    } catch (error) {
      console.error("An error occurred while requesting permission. ", error);
    }
  };

  const disableMessaging = async (): Promise<void> => {
    try {
      await handleFcmTokenReceived(token as string, DISABLED);
      await deleteToken(messaging);
      setToken(undefined);
      // Here you would remove token from server
    } catch (error) {
      console.error("An error occurred while deleting token. ", error);
    }
  };

  return (
    <MessagingContext.Provider
      value={{ enableMessaging, disableMessaging, enabled, token }}
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
