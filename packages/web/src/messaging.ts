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

const messaging = getMessaging(app);

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
        const token = await getToken(messaging, {
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
        await deleteToken(messaging);
      }
    })
    .catch(error => {
      console.error("Failed to delete Firebase token:", error);
    });
};

const registerServiceWorker = () => {
  return isSupported().then(async supported => {
    if (supported) {
      navigator.serviceWorker
        .register("/firebase-messaging-sw.js")
        .then(() => {
          console.log("Service worker registered successfully");
        })
        .catch(error => {
          console.error("Service worker registration failed:", error);
        });
    }
  });
};

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const onMessageReceived = (callback: (payload: any) => void) => {
  onMessage(messaging, payload => {
    callback(payload);
  });
};

export {
  getFirebaseToken as getToken,
  deleteFirebaseToken as deleteToken,
  onMessageReceived,
  registerServiceWorker,
};
