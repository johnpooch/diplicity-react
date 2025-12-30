import type { Preview } from "@storybook/react";
import "../src/index.css";
import withThemeProvider from "./with-theme-decorator";
import withRouter from "./with-router-decorator";
import withQueryClient from "./with-query-client-decorator";
import withRedux from "./with-redux-decorator";
import withMessaging from "./with-messaging-decorator";
import { initialize, mswLoader } from "msw-storybook-addon";

initialize({
  onUnhandledRequest: req => {
    const url = new URL(req.url);
    if (
      url.pathname.startsWith("/src/") ||
      url.pathname.includes("?import") ||
      url.pathname.includes("otto.png") ||
      url.pathname.includes("index.json")
    ) {
      return;
    }
    console.warn(
      `[MSW] Warning: intercepted a request without a matching request handler:\n\n  • ${req.method} ${req.url}`
    );
  },
});

const preview: Preview = {
  parameters: {
    controls: {
      matchers: {
        color: /(background|color)$/i,
        date: /Date$/i,
      },
    },
  },
  decorators: [withThemeProvider, withRouter, withQueryClient, withRedux, withMessaging],
  loaders: [mswLoader],
};

export default preview;
