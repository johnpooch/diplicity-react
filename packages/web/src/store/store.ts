import { combineReducers } from "redux";
import { configureStore } from "@reduxjs/toolkit";
import { feedbackSlice } from "./feedback";
import { authSlice } from "./auth";
import { service } from "./service";
import { api } from "./api";

const enhancedApi = api.enhanceEndpoints({
  addTagTypes: ["Device", "Game", "Channel", "Order", "PhaseState"],
  endpoints: {
    devicesList: {
      providesTags: ["Device"],
    },
    devicesCreate: {
      invalidatesTags: ["Device"],
    },
    gamesList: {
      providesTags: ["Game"],
    },
    gameRetrieve: {
      providesTags: ["Game"],
    },
    gameCreate: {
      invalidatesTags: ["Game"],
    },
    gamePhaseStatesList: {
      providesTags: ["PhaseState"],
    },
    gameConfirmPhasePartialUpdate: {
      invalidatesTags: ["Game", "PhaseState", "Order"],
    },
    gameResolvePhaseCreate: {
      invalidatesTags: ["Game", "PhaseState", "Order"],
    },
    gameJoinCreate: {
      invalidatesTags: ["Game"],
    },
    gameLeaveDestroy: {
      invalidatesTags: ["Game"],
    },
    gamesChannelsList: {
      providesTags: ["Channel"],
    },
    gamesChannelsCreateCreate: {
      invalidatesTags: ["Channel"],
    },
    gamesChannelsMessagesCreateCreate: {
      invalidatesTags: ["Channel"],
    },
    gameOrdersList: {
      providesTags: ["Order"],
    },
    gameOrdersCreate: {
      invalidatesTags: ["Order", "PhaseState"],
    },
    gameOrdersDeleteDestroy: {
      invalidatesTags: ["Order", "PhaseState"],
    },
    userRetrieve: {
      providesTags: ["User"],
    },
    userUpdatePartialUpdate: {
      invalidatesTags: ["User"],
    },
  },
});

const store = configureStore({
  reducer: combineReducers({
    auth: authSlice.reducer,
    feedback: feedbackSlice.reducer,
    [enhancedApi.reducerPath]: enhancedApi.reducer,
  }),
  middleware: getDefaultMiddleware =>
    getDefaultMiddleware().concat(service.middleware),
});

type RootState = ReturnType<(typeof store)["getState"]>;

export type { RootState };
export { store };
