import "./App.css";
import { useEffect } from "react";
import { GoogleOAuthProvider } from "@react-oauth/google";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import Router from "./Router";
import { MaintenanceMode } from "./components/MaintenanceMode";
import { ErrorBoundary } from "./components/ErrorBoundary";
import { AuthProvider, useAuth } from "./auth";
import { Toaster } from "./components/ui/sonner";
import { isNativePlatform } from "./utils/platform";
import { initializeNativeSocialLogin } from "./auth/nativeGoogleAuth";
import { App as CapacitorApp } from "@capacitor/app";
import { deepLinkStorage, parseDeepLinkUrl } from "./deepLink";

const queryClient = new QueryClient();

function AppContent() {
  const { loggedIn } = useAuth();

  return <Router loggedIn={loggedIn} queryClient={queryClient} />;
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
                duration={1000}
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
