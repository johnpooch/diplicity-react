import { useEffect, useRef } from "react";
import { useAuth } from "@/auth";
import { useGamesList } from "@/api/generated/endpoints";
import { isNativePlatform } from "@/utils/platform";
import { useCheckNotificationPermission } from "./useCheckNotificationPermission";

const useNotificationPermissionPrompt = () => {
  const { loggedIn } = useAuth();
  const native = isNativePlatform();
  const hasPromptedRef = useRef(false);
  const checkNotificationPermission = useCheckNotificationPermission();

  const { data: activeGamesData } = useGamesList(
    { mine: true, status: "active", sandbox: false },
    { query: { enabled: loggedIn && native } }
  );

  useEffect(() => {
    if (!native || !loggedIn || hasPromptedRef.current) return;
    if (activeGamesData === undefined) return;
    if (activeGamesData.count === 0) return;

    hasPromptedRef.current = true;
    checkNotificationPermission();
  }, [native, loggedIn, activeGamesData, checkNotificationPermission]);
};

export { useNotificationPermissionPrompt };
