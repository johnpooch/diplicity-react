import { createListenerMiddleware, isRejected, isRejectedWithValue } from "@reduxjs/toolkit";
import { authActions } from "./auth";
import { telemetryService } from "../../services";

const listenerMiddleware = createListenerMiddleware();

listenerMiddleware.startListening({
    matcher: isRejected,
    effect: async (action) => {
        telemetryService.logError(action.error as Error);
    },
});

listenerMiddleware.startListening({
    matcher: isRejectedWithValue,
    effect: async (action, listenerApi) => {
        const typedAction = action as { payload?: { status: number } };
        if (typedAction.payload?.status === 401) {
            listenerApi.dispatch(authActions.logout());
        }
    },
});

export default listenerMiddleware;
