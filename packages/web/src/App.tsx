import "./App.css";
import { GoogleOAuthProvider } from "@react-oauth/google";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import Router from "./Router";
import { MaintenanceMode } from "./components/MaintenanceMode";
import { ErrorBoundary } from "./components/ErrorBoundary";
import { MessagingContextProvider } from "./context";
import { AuthProvider, useAuth } from "./auth";
import { Toaster } from "./components/ui/sonner";

const queryClient = new QueryClient();

function AppContent() {
  const { loggedIn } = useAuth();

  return (
    <MessagingContextProvider>
      <Router loggedIn={loggedIn} queryClient={queryClient} />
    </MessagingContextProvider>
  );
}

function App() {
  const isMaintenanceMode = import.meta.env.VITE_MAINTENANCE_MODE === "true";

  return (
    <ErrorBoundary>
      {isMaintenanceMode ? (
        <MaintenanceMode />
      ) : (
        <GoogleOAuthProvider clientId={import.meta.env.VITE_GOOGLE_CLIENT_ID}>
          <QueryClientProvider client={queryClient}>
            <AuthProvider>
              <AppContent />
              <Toaster position="top-center" closeButton richColors />
            </AuthProvider>
          </QueryClientProvider>
        </GoogleOAuthProvider>
      )}
    </ErrorBoundary>
  );
}

export default App;
