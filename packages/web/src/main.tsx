import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";
import "@fontsource/roboto/300.css";
import "@fontsource/roboto/400.css";
import "@fontsource/roboto/500.css";
import "@fontsource/roboto/700.css";
import App from "./App.tsx";
import { SplashScreen } from "@capacitor/splash-screen";
import { initializeObservability } from "./observability";
import { initializeSentry } from "./sentry";
import { themeStorage } from "./theme/themeStorage";
import { isNativePlatform } from "./utils/platform";
import { reloadForStaleChunk } from "./utils/staleChunk";

if (isNativePlatform()) {
  setTimeout(() => SplashScreen.hide(), 10000);
}

themeStorage.initialize();
initializeObservability();
initializeSentry();

window.addEventListener("vite:preloadError", (event) => {
  event.preventDefault();
  reloadForStaleChunk();
});

const enableMocking = async () => {
  if (import.meta.env.VITE_MOCKS !== "true") return;
  const { startMocks } = await import("./mocks/browser");
  await startMocks();
};

enableMocking().then(() => {
  createRoot(document.getElementById("root")!).render(
    <StrictMode>
      <App />
    </StrictMode>
  );
});
