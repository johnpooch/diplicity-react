import type { Preview } from "@storybook/react";
import "../src/index.css";
import withRouter from "./with-router-decorator";
import withQueryClient from "./with-query-client-decorator";

const preview: Preview = {
  parameters: {
    controls: {
      matchers: {
        color: /(background|color)$/i,
        date: /Date$/i,
      },
    },
  },
  decorators: [withRouter, withQueryClient],
};

export default preview;
