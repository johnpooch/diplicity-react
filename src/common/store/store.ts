import { AnyAction, combineReducers } from "redux";
import service from "./service";
import {
    authSlice,
} from "./auth";
import { configureStore, ThunkDispatch } from "@reduxjs/toolkit";
import { IAuthService } from "../services";

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
            [service.reducerPath]: service.reducer
        }),
        middleware: getDefaultMiddleware =>
            getDefaultMiddleware({ thunk: { extraArgument: { authService } } })
                .concat(
                    service.middleware
                )
    });
};

export type RootState = ReturnType<ReturnType<typeof createStore>["getState"]>;
export type AppDispatch = ThunkDispatch<RootState, ThunkApiExtraArguments, AnyAction>;