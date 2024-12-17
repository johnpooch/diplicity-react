import { Decorator } from "@storybook/react";
import { MemoryRouter } from "react-router";

const withRouterDecorator: Decorator = (Story) => (
  <MemoryRouter>
    <Story />
  </MemoryRouter>
);

export { withRouterDecorator };
