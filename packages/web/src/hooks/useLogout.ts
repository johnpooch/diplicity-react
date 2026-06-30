import { useAuth } from "../auth";
import { useMessaging } from "./useMessaging";

const useLogout = (): (() => Promise<void>) => {
  const { logout } = useAuth();
  const { disableMessaging } = useMessaging();

  return async () => {
    await disableMessaging();
    logout();
  };
};

export { useLogout };
