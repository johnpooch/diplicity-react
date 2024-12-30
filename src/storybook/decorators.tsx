import { Decorator } from "@storybook/react";
import { MemoryRouter } from "react-router";

const withRouterDecorator: Decorator = (Story) => (
  <MemoryRouter>
    <Story />
  </MemoryRouter>
);

const withFullScreenContainerDecorator: Decorator = (Story) => (
  <div
    style={{
      width: "100vw",
      height: "100vh",
      display: "flex",
      justifyContent: "center",
      alignItems: "center",
    }}
  >
    <Story />
  </div>
);

export { withRouterDecorator, withFullScreenContainerDecorator };
