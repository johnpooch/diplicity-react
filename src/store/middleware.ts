import { createListenerMiddleware, isRejectedWithValue } from "@reduxjs/toolkit";
import { isUnauthorized } from "./matchers";
import { authSlice } from "./auth";

const listenerMiddleware = createListenerMiddleware();

// listenerMiddleware.startListening({
//     matcher: isRejected,
//     effect: async (action) => {
//         if (!isUnauthorized(action)) {
//             telemetryService.logError(action.error as Error);
//         }
//     },
// });

listenerMiddleware.startListening({
    matcher: isRejectedWithValue,
    effect: async (action, listenerApi) => {
        if (isUnauthorized(action)) {
            listenerApi.dispatch(authSlice.actions.logout());
        }
    },
});

export { listenerMiddleware };
