import { FirebaseMessaging } from "@capacitor-firebase/messaging";

export const checkPermission = async (): Promise<
  "granted" | "denied" | "prompt"
> => {
  const { receive } = await FirebaseMessaging.checkPermissions();
  if (receive === "granted" || receive === "denied") return receive;
  return "prompt";
};

export const requestPermission = async (): Promise<"granted" | "denied"> => {
  const { receive } = await FirebaseMessaging.requestPermissions();
  return receive === "granted" ? "granted" : "denied";
};

export const getToken = async (): Promise<string | null> => {
  try {
    const { token } = await FirebaseMessaging.getToken();
    return token;
  } catch {
    return null;
  }
};

export const addTokenRefreshListener = (
  callback: (token: string) => void
) => {
  return FirebaseMessaging.addListener("tokenReceived", (event) => {
    callback(event.token);
  });
};

export const addNotificationReceivedListener = (callback: () => void) => {
  return FirebaseMessaging.addListener("notificationReceived", () => {
    callback();
  });
};
