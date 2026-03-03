import { useEffect, useSyncExternalStore } from "react";
import { useNavigate } from "react-router";
import { deepLinkStorage } from "./deepLinkStorage";

export const useDeepLink = () => {
  const navigate = useNavigate();
  const pendingPath = useSyncExternalStore(
    deepLinkStorage.subscribe,
    deepLinkStorage.getPendingPath
  );

  useEffect(() => {
    if (pendingPath) {
      const path = deepLinkStorage.consumePendingPath();
      if (path) {
        navigate(path, { replace: true });
      }
    }
  }, [pendingPath, navigate]);
};
