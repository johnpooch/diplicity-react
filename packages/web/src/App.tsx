import "./App.css";
import { CssBaseline, ThemeProvider } from "@mui/material";
import { Provider, useSelector } from "react-redux";
import { GoogleOAuthProvider } from "@react-oauth/google";
import Router from "./Router";
import theme from "./theme";
import { Feedback } from "./components/Feedback";
import { MaintenanceMode } from "./components/MaintenanceMode";
import { MessagingContextProvider } from "./context";
import { store, selectAuth } from "./store";

function AppContent() {
  const { loggedIn } = useSelector(selectAuth);

  return (
    <MessagingContextProvider>
      <Router loggedIn={loggedIn} />
      <Feedback />
    </MessagingContextProvider>
  );
}

function App() {
  const isMaintenanceMode = import.meta.env.VITE_MAINTENANCE_MODE === "true";

  if (isMaintenanceMode) {
    return (
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <MaintenanceMode />
      </ThemeProvider>
    );
  }

  return (
    <GoogleOAuthProvider clientId={import.meta.env.VITE_GOOGLE_CLIENT_ID}>
      <Provider store={store}>
        <CssBaseline />
        <ThemeProvider theme={theme}>
          <AppContent />
        </ThemeProvider>
      </Provider>
    </GoogleOAuthProvider>
  );
}

export default App;
