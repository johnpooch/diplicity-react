import { useEffect, useState } from "react";
import { Network } from "@capacitor/network";

export const useNetworkStatus = (): boolean => {
  const [online, setOnline] = useState(true);

  useEffect(() => {
    let active = true;

    Network.getStatus().then((status) => {
      if (active) setOnline(status.connected);
    });

    const handle = Network.addListener("networkStatusChange", (status) => {
      if (active) setOnline(status.connected);
    });

    return () => {
      active = false;
      handle.then((listener) => listener.remove());
    };
  }, []);

  return online;
};
