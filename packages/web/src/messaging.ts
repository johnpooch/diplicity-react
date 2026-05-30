import { initializeApp } from "firebase/app";
import {
  deleteToken,
  getMessaging,
  getToken,
  onMessage,
  isSupported,
} from "firebase/messaging";

const VAPID_KEY =
  "BDzNEIDfAnaXQ3O6tZqAq2rtQw5lFDxhMHJYalOPHVpNXBLeWuuFCK42OdLHzVIBEIsjEEfxzGGQS2jcT3Wfa-8";

const firebaseConfig = {
  apiKey: "AIzaSyDjCW9a1Y7wPTIQVyL_DMHmo61TzVFjx1c",
  authDomain: "diplicity-react.firebaseapp.com",
  projectId: "diplicity-react",
  storageBucket: "diplicity-react.firebasestorage.app",
  messagingSenderId: "919095022177",
  appId: "1:919095022177:web:6303772970effd99759020",
};

const app = initializeApp(firebaseConfig);

let messagingInstance: ReturnType<typeof getMessaging> | null = null;

const getMessagingInstance = () => {
  if (!messagingInstance) {
    messagingInstance = getMessaging(app);
  }
  return messagingInstance;
};

const getFirebaseToken = async () => {
  // Test hook: bypass Firebase SDK in E2E tests
  const testToken = (window as unknown as Record<string, unknown>).__TEST_FCM_TOKEN;
  if (typeof testToken === "string") {
    return testToken;
  }
  return isSupported()
    .then(async supported => {
      if (supported) {
        const registration = await navigator.serviceWorker.getRegistration();
        if (!registration) {
          throw new Error("Service worker registration not found");
        }
        const token = await getToken(getMessagingInstance(), {
          vapidKey: VAPID_KEY,
          serviceWorkerRegistration: registration,
        });
        return token;
      } else {
        return null;
      }
    })
    .catch(error => {
      console.error("Failed to get Firebase token:", error);
      return null;
    });
};

const deleteFirebaseToken = async () => {
  isSupported()
    .then(async supported => {
      if (supported) {
        const registration = await navigator.serviceWorker.getRegistration();
        if (!registration) {
          throw new Error("Service worker registration not found");
        }
        await deleteToken(getMessagingInstance());
      }
    })
    .catch(error => {
      console.error("Failed to delete Firebase token:", error);
    });
};

const registerServiceWorker = async () => {
  const supported = await isSupported();
  if (!supported) return;
  try {
    await navigator.serviceWorker.register("/firebase-messaging-sw.js");
  } catch (error) {
    console.error("Service worker registration failed:", error);
  }
};

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const onMessageReceived = (callback: (payload: any) => void) => {
  isSupported().then(supported => {
    if (supported) {
      onMessage(getMessagingInstance(), payload => {
        callback(payload);
      });
    }
  });
};

const onNotificationClick = (callback: (link: string) => void): (() => void) => {
  if (!("serviceWorker" in navigator)) return () => {};
  const handler = (event: MessageEvent) => {
    if (event.data?.type === "NOTIFICATION_CLICK" && event.data.link) {
      callback(event.data.link as string);
    }
  };
  navigator.serviceWorker.addEventListener("message", handler);
  return () => navigator.serviceWorker.removeEventListener("message", handler);
};

export {
  getFirebaseToken as getToken,
  deleteFirebaseToken as deleteToken,
  onMessageReceived,
  onNotificationClick,
  registerServiceWorker,
};
