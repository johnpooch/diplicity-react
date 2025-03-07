import "./App.css";
import { CssBaseline, ThemeProvider } from "@mui/material";
import { Provider } from "react-redux";
import Router from "./Router";
import theme from "./theme";
import { AuthService } from "./services";
import { createStore } from "./common";
import { authActions } from "./common/store/auth";
import { Feedback } from "./components/feedback";
import { MessagingContextProvider } from "./context";

function App() {
  const url = new URL(window.location.href);
  const token = url.searchParams.get("token");

  const store = createStore({ authService: AuthService });

  if (token) {
    store.dispatch(authActions.login(token));
  }

  return (
    <Provider store={store}>
      <CssBaseline />
      <ThemeProvider theme={theme}>
        <MessagingContextProvider>
          <Router />
          <Feedback />
        </MessagingContextProvider>
      </ThemeProvider>
    </Provider>
  );
}

export default App;
