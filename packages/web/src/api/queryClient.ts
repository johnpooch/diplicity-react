import { QueryClient, focusManager } from "@tanstack/react-query";
import { App as CapacitorApp } from "@capacitor/app";
import { isNativePlatform } from "../utils/platform";

if (isNativePlatform()) {
  focusManager.setEventListener(handleFocus => {
    const listener = CapacitorApp.addListener(
      "appStateChange",
      ({ isActive }) => handleFocus(isActive)
    );
    return () => {
      void listener.then(handle => handle.remove());
    };
  });
}

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5,
      gcTime: 1000 * 60 * 10,
      refetchOnWindowFocus: false,
      retry: 1,
    },
    mutations: {
      retry: 0,
    },
  },
});
