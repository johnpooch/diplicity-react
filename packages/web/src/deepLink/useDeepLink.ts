import { useEffect, useSyncExternalStore } from "react";
import { useNavigate } from "react-router";
import { deepLinkStorage } from "./deepLinkStorage";

const canOpenAnyPath = () => true;

export const useDeepLink = (
  canOpen: (path: string) => boolean = canOpenAnyPath
) => {
  const navigate = useNavigate();
  const pendingPath = useSyncExternalStore(
    deepLinkStorage.subscribe,
    deepLinkStorage.getPendingPath
  );

  useEffect(() => {
    if (pendingPath && canOpen(pendingPath)) {
      const path = deepLinkStorage.consumePendingPath();
      if (path) {
        navigate(path, { replace: true });
      }
    }
  }, [pendingPath, canOpen, navigate]);
};
