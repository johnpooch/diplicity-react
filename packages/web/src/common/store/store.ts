import { AnyAction, combineReducers } from "redux";
import service from "./service";
import {
    authSlice,
} from "./auth";
import { configureStore, ThunkDispatch } from "@reduxjs/toolkit";
import { IAuthService } from "../services";
import listenerMiddleware from "./middleware";
import { feedbackSlice } from "./feedback";

type CreateStoreOptions = {
    authService: IAuthService;
};

export type ThunkApiExtraArguments = {
    authService: IAuthService;
};

export const createStore = ({
    authService,
}: CreateStoreOptions) => {
    return configureStore({
        reducer: combineReducers({
            auth: authSlice.reducer,
            feedback: feedbackSlice.reducer,
            [service.reducerPath]: service.reducer
        }),
        middleware: getDefaultMiddleware =>
            getDefaultMiddleware({ thunk: { extraArgument: { authService } } })
                .concat(
                    service.middleware,
                    listenerMiddleware.middleware
                )
    });
};

export type RootState = ReturnType<ReturnType<typeof createStore>["getState"]>;
export type AppDispatch = ThunkDispatch<RootState, ThunkApiExtraArguments, AnyAction>;
