import { useEffect, useRef } from "react";
import { useAuth } from "@/auth";
import { useGamesListSuspense } from "@/api/generated/endpoints";
import { useCheckNotificationPermission } from "./useCheckNotificationPermission";

const useNotificationPermissionPrompt = () => {
  const { loggedIn } = useAuth();
  const hasPromptedRef = useRef(false);
  const checkNotificationPermission = useCheckNotificationPermission();

  const { data: activeGamesData } = useGamesListSuspense(
    { mine: true, status: "active", sandbox: false },
    { query: { enabled: loggedIn } }
  );

  useEffect(() => {
    if (!loggedIn || hasPromptedRef.current) return;
    if (activeGamesData === undefined) return;
    if (activeGamesData.count === 0) return;

    hasPromptedRef.current = true;
    checkNotificationPermission();
  }, [loggedIn, activeGamesData, checkNotificationPermission]);
};

export { useNotificationPermissionPrompt };
