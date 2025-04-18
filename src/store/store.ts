import { combineReducers } from "redux";
import { configureStore } from "@reduxjs/toolkit";
import { listenerMiddleware } from "./middleware";
import { feedbackSlice } from "./feedback";
import { authSlice } from "./auth";
import { service } from "./service";

const store = configureStore({
    reducer: combineReducers({
        auth: authSlice.reducer,
        feedback: feedbackSlice.reducer,
        [service.reducerPath]: service.reducer
    }),
    middleware: getDefaultMiddleware =>
        getDefaultMiddleware()
            .concat(
                service.middleware,
                listenerMiddleware.middleware
            )
});

type RootState = ReturnType<typeof store["getState"]>;

export type { RootState }
export { store };
