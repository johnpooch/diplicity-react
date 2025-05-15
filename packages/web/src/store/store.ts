import { combineReducers } from "redux";
import { configureStore } from "@reduxjs/toolkit";
import { listenerMiddleware } from "./middleware";
import { feedbackSlice } from "./feedback";
import { authSlice } from "./auth";
import { service } from "./service";
import { api } from "./api";
import { orderSlice } from "./order";

const enhancedApi = api.enhanceEndpoints({
    addTagTypes: ['Device', 'Game', 'Channel', 'Order'],
    endpoints: {
        devicesList: {
            providesTags: ['Device'],
        },
        devicesCreate: {
            invalidatesTags: ['Device'],
        },
        gamesList: {
            providesTags: ['Game'],
        },
        gameRetrieve: {
            providesTags: ['Game'],
        },
        gameCreate: {
            invalidatesTags: ['Game'],
        },
        gameConfirmCreate: {
            invalidatesTags: ['Game'],
        },
        gameJoinCreate: {
            invalidatesTags: ['Game'],
        },
        gameLeaveDestroy: {
            invalidatesTags: ['Game'],
        },
        gameChannelsList: {
            providesTags: ['Channel'],
        },
        gameChannelCreate: {
            invalidatesTags: ['Channel'],
        },
        gameChannelCreate2: {
            invalidatesTags: ['Channel'],
        },
        gamePhaseOrdersList: {
            providesTags: ['Order'],
        },
        gameOrderCreate: {
            invalidatesTags: ['Order'],
        },
    },
})

const store = configureStore({
    reducer: combineReducers({
        auth: authSlice.reducer,
        feedback: feedbackSlice.reducer,
        order: orderSlice.reducer,
        [enhancedApi.reducerPath]: enhancedApi.reducer
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
