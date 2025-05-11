import { combineReducers } from "redux";
import { configureStore } from "@reduxjs/toolkit";
import { listenerMiddleware } from "./middleware";
import { feedbackSlice } from "./feedback";
import { authSlice } from "./auth";
import { service } from "./service";
import { api } from "./api";

const enhancedApi = api.enhanceEndpoints({
    addTagTypes: ['Device', 'Game', 'Channel'],
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
        gameChannelMessageCreate: {
            invalidatesTags: ['Channel'],
        },
    },
})

const store = configureStore({
    reducer: combineReducers({
        auth: authSlice.reducer,
        feedback: feedbackSlice.reducer,
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
