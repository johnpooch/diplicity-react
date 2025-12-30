import React from "react";
import { MemoryRouter, Routes, Route } from "react-router";
import type { DecoratorFunction } from "@storybook/csf";
import type { ReactRenderer } from "@storybook/react";

const withRouter: DecoratorFunction<ReactRenderer> = (Story, context) => {
  const initialEntries = context.parameters.router?.initialEntries || ["/"];
  const path = context.parameters.router?.path || "/";

  return (
    <MemoryRouter initialEntries={initialEntries}>
      <Routes>
        <Route path={path} element={<Story />} />
      </Routes>
    </MemoryRouter>
  );
};

export default withRouter;
