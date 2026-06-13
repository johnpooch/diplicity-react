import { Capacitor } from "@capacitor/core";

export const isNativePlatform = (): boolean => {
  return Capacitor.isNativePlatform();
};

export const isIosPlatform = (): boolean => {
  return Capacitor.getPlatform() === "ios";
};
