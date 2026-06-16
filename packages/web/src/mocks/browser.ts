import { setupWorker } from "msw/browser";
import { tokenStorage } from "@/auth/tokenStorage";
import { handlers } from "./handlers";

export const startMocks = async () => {
  if (
    !tokenStorage.isLoggedIn() &&
    localStorage.getItem("mock:loggedOut") !== "true"
  ) {
    tokenStorage.setTokens({
      accessToken: "mock-access-token",
      refreshToken: "mock-refresh-token",
      email: "mock.player@example.com",
      name: "Mock Player",
    });
  }

  const worker = setupWorker(...handlers);
  const started = worker.start({
    onUnhandledRequest: (request, print) => {
      const url = new URL(request.url);
      if (
        url.pathname.startsWith("/src/") ||
        url.pathname.startsWith("/node_modules/") ||
        url.pathname.startsWith("/@") ||
        url.origin !== window.location.origin
      ) {
        return;
      }
      print.warning();
    },
  });
  await started;

  // worker.start() can resolve slightly before the service worker actually
  // intercepts this client's requests; without this probe the router's first
  // data loads race past MSW and hit the Vite SPA fallback (HTML) instead.
  for (let attempt = 0; attempt < 50; attempt++) {
    try {
      const response = await fetch("/version/", { cache: "no-store" });
      const contentType = response.headers.get("content-type") ?? "";
      if (response.ok && contentType.includes("application/json")) return;
    } catch {
      // retry
    }
    await new Promise(resolve => setTimeout(resolve, 100));
  }
  throw new Error("MSW worker did not start intercepting requests");
};
