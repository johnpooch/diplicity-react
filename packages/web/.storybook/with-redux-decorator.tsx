import React from "react";
import { Provider } from "react-redux";
import { combineReducers, configureStore } from "@reduxjs/toolkit";
import type { DecoratorFunction } from "@storybook/csf";
import type { ReactRenderer } from "@storybook/react";
import { feedbackSlice, authSlice, service } from "../src/store";

const withRedux: DecoratorFunction<ReactRenderer> = Story => {
  const store = configureStore({
    reducer: combineReducers({
      auth: authSlice.reducer,
      feedback: feedbackSlice.reducer,
      [service.reducerPath]: service.reducer,
    }),
    middleware: getDefaultMiddleware =>
      getDefaultMiddleware().concat(service.middleware),
  });

  return (
    <Provider store={store}>
      <Story />
    </Provider>
  );
};

export default withRedux;
