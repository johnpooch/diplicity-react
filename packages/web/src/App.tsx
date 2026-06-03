import "./App.css";
import { useEffect, Suspense } from "react";
import { GoogleOAuthProvider } from "@react-oauth/google";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import Router from "./Router";
import { MaintenanceMode } from "./components/MaintenanceMode";
import { ErrorBoundary } from "./components/ErrorBoundary";
import { AuthProvider } from "./auth";
import { Toaster } from "./components/ui/sonner";
import { isNativePlatform } from "./utils/platform";
import { initializeNativeSocialLogin } from "./auth/nativeGoogleAuth";
import { App as CapacitorApp } from "@capacitor/app";
import { deepLinkStorage, parseDeepLinkUrl } from "./deepLink";
import { onNotificationClick } from "./messaging";
import { addNotificationTapListener } from "./messaging-native";
import { getVariantsListQueryKey } from "./api/generated/endpoints";
import { useNotificationPermissionPrompt } from "./hooks/useNotificationPermissionPrompt";

const queryClient = new QueryClient();

// Variants are essentially static reference data (published variants almost
// never change; drafts only change when the owner edits them). Combined with
// the server's ETag/Cache-Control on GET /variants/, an hour-long staleTime
// keeps the React Query cache warm across navigations without losing
// freshness for the rare update.
queryClient.setQueryDefaults(getVariantsListQueryKey(), {
  staleTime: 60 * 60 * 1000,
});

const NotificationPermissionPrompter: React.FC = () => {
  useNotificationPermissionPrompt();
  return null;
};

function AppContent() {
  return (
    <>
      <Suspense fallback={null}>
        <NotificationPermissionPrompter />
      </Suspense>
      <Router queryClient={queryClient} />
    </>
  );
}

const MaybeGoogleOAuthProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  if (isNativePlatform()) {
    return <>{children}</>;
  }
  return (
    <GoogleOAuthProvider clientId={import.meta.env.VITE_GOOGLE_CLIENT_ID}>
      {children}
    </GoogleOAuthProvider>
  );
};

function App() {
  const isMaintenanceMode = import.meta.env.VITE_MAINTENANCE_MODE === "true";

  useEffect(() => {
    if (isNativePlatform()) {
      initializeNativeSocialLogin();
    }
  }, []);

  useEffect(() => {
    if (!isNativePlatform()) return;

    const listener = CapacitorApp.addListener("appUrlOpen", (event) => {
      const path = parseDeepLinkUrl(event.url);
      if (path) deepLinkStorage.setPendingPath(path);
    });

    CapacitorApp.getLaunchUrl().then((result) => {
      if (result?.url) {
        const path = parseDeepLinkUrl(result.url);
        if (path) deepLinkStorage.setPendingPath(path);
      }
    });

    return () => {
      listener.then((handle) => handle.remove());
    };
  }, []);

  useEffect(() => {
    const handleLink = (link: string) => {
      const path = parseDeepLinkUrl(link);
      if (path) deepLinkStorage.setPendingPath(path);
    };

    if (isNativePlatform()) {
      const listener = addNotificationTapListener(handleLink);
      return () => {
        listener.then((l) => l.remove());
      };
    } else {
      return onNotificationClick(handleLink);
    }
  }, []);

  return (
    <ErrorBoundary>
      {isMaintenanceMode ? (
        <MaintenanceMode />
      ) : (
        <MaybeGoogleOAuthProvider>
          <QueryClientProvider client={queryClient}>
            <AuthProvider>
              <AppContent />
              <Toaster
                position="top-center"
                closeButton
                richColors
                duration={1200}
                mobileOffset={{ top: "calc(72px + env(safe-area-inset-top, 0px))" }}
              />
            </AuthProvider>
          </QueryClientProvider>
        </MaybeGoogleOAuthProvider>
      )}
    </ErrorBoundary>
  );
}

export default App;
