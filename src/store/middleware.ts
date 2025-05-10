import { createListenerMiddleware, isRejectedWithValue } from "@reduxjs/toolkit";
import { isUnauthorized } from "./matchers";
import { authSlice } from "./auth";
import { RootState } from "./store";
import { service } from "./service";

const listenerMiddleware = createListenerMiddleware();

// listenerMiddleware.startListening({
//     matcher: isRejected,
//     effect: async (action) => {
//         if (!isUnauthorized(action)) {
//             telemetryService.logError(action.error as Error);
//         }
//     },
// });

export { listenerMiddleware };
