import "./App.css";
import { CssBaseline, ThemeProvider } from "@mui/material";
import { Provider } from "react-redux";
import { GoogleOAuthProvider } from "@react-oauth/google";
import Router from "./Router";
import theme from "./theme";
import { Feedback } from "./components/Feedback";
import { MessagingContextProvider } from "./context";
import { store } from "./store";

function App() {

  return (
    <GoogleOAuthProvider clientId={import.meta.env.VITE_GOOGLE_CLIENT_ID}>
      <Provider store={store}>
        <CssBaseline />
        <ThemeProvider theme={theme}>
          <MessagingContextProvider>
            <Router />
            <Feedback />
          </MessagingContextProvider>
        </ThemeProvider>
      </Provider>
    </GoogleOAuthProvider>
  );
}

export default App;
