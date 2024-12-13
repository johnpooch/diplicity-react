import { createListenerMiddleware, isRejectedWithValue } from "@reduxjs/toolkit";
import { authActions } from "./auth";

const listenerMiddleware = createListenerMiddleware();

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
