import {
    createAsyncThunk,
    createSlice,
} from "@reduxjs/toolkit";
import { RootState } from "./store";
import { ThunkApiExtraArguments } from "./store";

type Auth = {
    token: string | null;
    loggedIn: boolean;
};

const login = createAsyncThunk("auth/login", async (token: string, { extra }) => {
    await (extra as ThunkApiExtraArguments).authService.setTokenInStorage(token);
    return token;
});

const logout = createAsyncThunk("auth/logout", async (_, { extra }) => {
    await (extra as ThunkApiExtraArguments).authService.removeTokenFromStorage();
});

export const authSlice = createSlice({
    name: "auth",
    initialState: { token: null, loggedIn: false } as Auth,
    reducers: {},
    extraReducers: (builder) => {
        builder.addMatcher(login.fulfilled.match, (state, { payload }) => {
            return { ...state, token: payload, loggedIn: true };
        });
        builder.addMatcher(logout.fulfilled.match, (state) => {
            return { ...state, token: null, loggedIn: false };
        });
    },
});

export const selectAuth = (state: RootState) => state.auth;