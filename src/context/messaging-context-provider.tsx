import { createContext, useContext, useEffect, useState } from "react";
import { initializeApp } from "firebase/app";
import {
  getToken,
  onMessage,
  getMessaging,
  deleteToken,
} from "firebase/messaging";
import { useFcmTokenReceivedMutation } from "../common";

// const firebaseConfig = {
//   apiKey: "AIzaSyDjCW9a1Y7wPTIQVyL_DMHmo61TzVFjx1c",
//   authDomain: "diplicity-react.firebaseapp.com",
//   projectId: "diplicity-react",
//   storageBucket: "diplicity-react.firebasestorage.app",
//   messagingSenderId: "919095022177",
//   appId: "1:919095022177:web:6303772970effd99759020",
// };

// Diplicity engine
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

// diplicity-engine
const VAPID_KEY =
  "BFb1kkti2UR4oxC9K5HAAIwH-KOcwGBnZIEvUM9yzD7ppPWK6M4_AlpjfC5m5iQyFd4VqsBgSA5nfSEGbjlUtaY";

// diplicity-react
// const VAPID_KEY =
//   "BDzNEIDfAnaXQ3O6tZqAq2rtQw5lFDxhMHJYalOPHVpNXBLeWuuFCK42OdLHzVIBEIsjEEfxzGGQS2jcT3Wfa-8";

// Register the service worker
navigator.serviceWorker
  .register("/firebase-messaging-sw.js")
  .then((registration) => {
    console.log(registration);
    console.log("Service worker registered with scope:", registration.scope);

    //Get the token after registration is successful
    getToken(messaging, {
      vapidKey: VAPID_KEY,
    })
      .then((currentToken) => {
        if (currentToken) {
          // Send the token to your server
        } else {
          // Show permission request UI
          console.log(
            "No registration token available. Request permission to generate one."
          );
          // ... your logic to request notification permission ...
        }
      })
      .catch((err) => {
        console.log("An error occurred while retrieving token. ", err);
      });
  })
  .catch((error) => {
    console.error("Service worker registration failed:", error);
  });

onMessage(messaging, async (payload) => {
  console.log("Message received. ", payload);
});

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
        if (currentToken) {
          await handleFcmTokenReceived(currentToken, ENABLED);
        }
        // Here you would send token to server
        console.log("Token retrieved:", currentToken);
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

    // const unsubscribe = onMessage(messaging, (payload) => {
    //   console.log("Message received. ", payload);
    // });

    // return () => {
    //   unsubscribe();
    // };
  }, []);

  const enableMessaging = async (): Promise<void> => {
    try {
      const permission = await Notification.requestPermission();
      if (permission === "granted") {
        await retrieveToken();
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
      console.log("Getting token");
      await handleFcmTokenReceived(token as string, DISABLED);
      console.log("Deleting token");
      await deleteToken(messaging);
      console.log("Token deleted");
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
