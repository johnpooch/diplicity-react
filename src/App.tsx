import "./App.css";
import { Box, CssBaseline, Modal, ThemeProvider } from "@mui/material";
import { Provider } from "react-redux";
import Router from "./Router";
import theme from "./theme";
import { AuthService } from "./services";
import { createStore } from "./common";
import { authActions } from "./common/store/auth";
import ConnectedFeedbackComponent from "./components/Feedback";
import { GlobalModalProvider, useGlobalModal } from "./GlobalModalContext";
import { PlayerInfo } from "./components/PlayerInfo";
import { GameInfo } from "./components/GameInfo";

const modalBoxStyle = {
  position: "absolute",
  top: "50%",
  left: "50%",
  transform: "translate(-50%, -50%)",
  width: 400,
  bgcolor: "background.paper",
  border: "2px solid #000",
  boxShadow: 24,
  p: 4,
};

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
        <GlobalModalProvider>
          <Router />
          <ConnectedFeedbackComponent />
          <GlobalModals />
        </GlobalModalProvider>
      </ThemeProvider>
    </Provider>
  );
}

const GlobalModals = () => {
  const { modalType, modalId, closeModal } = useGlobalModal();

  return (
    <>
      {modalType === "playerInfo" && modalId && (
        <Modal open={!!modalId} onClose={closeModal}>
          <Box sx={modalBoxStyle}>
            <PlayerInfo gameId={modalId} />
          </Box>
        </Modal>
      )}
      {modalType === "gameInfo" && modalId && (
        <Modal open={!!modalId} onClose={closeModal}>
          <Box sx={modalBoxStyle}>
            <GameInfo gameId={modalId} />
          </Box>
        </Modal>
      )}
      {/* Add other modals here */}
    </>
  );
};

export default App;
