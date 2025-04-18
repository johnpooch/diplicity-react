import { createListenerMiddleware, isRejected, isRejectedWithValue } from "@reduxjs/toolkit";
import { authActions } from "./auth";
import { telemetryService } from "../../services";
import { isUnauthorized } from "./matchers";
import service from "./service";

const listenerMiddleware = createListenerMiddleware();

listenerMiddleware.startListening({
    matcher: service.endpoints.login.matchFulfilled,
    effect: async (action, listenerApi) => {
        listenerApi.dispatch(authActions.login(action.payload));
    }
});

listenerMiddleware.startListening({
    matcher: isRejected,
    effect: async (action) => {
        if (!isUnauthorized(action)) {
            telemetryService.logError(action.error as Error);
        }
    },
});

listenerMiddleware.startListening({
    matcher: isRejectedWithValue,
    effect: async (action, listenerApi) => {
        if (isUnauthorized(action)) {
            listenerApi.dispatch(authActions.logout());
        }
    },
});

export default listenerMiddleware;
