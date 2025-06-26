import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import { service } from "./service";

type Auth = {
    loggedIn: boolean;
    accessToken: string | null;
    refreshToken: string | null;
    email: string | null;
    username: string | null;
}

const initialState: Auth = {
    accessToken: localStorage.getItem("accessToken"),
    refreshToken: localStorage.getItem("refreshToken"),
    email: localStorage.getItem("email"),
    username: localStorage.getItem("username"),
    loggedIn: !!localStorage.getItem("accessToken"),
};

const authSlice = createSlice({
    name: "auth",
    initialState,
    reducers: {
        logout: () => {
            localStorage.removeItem("accessToken");
            localStorage.removeItem("refreshToken");
            localStorage.removeItem("email");
            localStorage.removeItem("username");
            return {
                loggedIn: false,
                accessToken: null,
                refreshToken: null,
                email: null,
                username: null,
            };
        },
        updateAccessToken: (state, action: PayloadAction<string>) => {
            localStorage.setItem("accessToken", action.payload);
            return { ...state, accessToken: action.payload };
        }
    },
    extraReducers: (builder) => {
        builder.addMatcher(service.endpoints.authLoginCreate.matchFulfilled, (state, { payload }) => {
            localStorage.setItem("accessToken", payload.accessToken);
            localStorage.setItem("refreshToken", payload.refreshToken);
            localStorage.setItem("email", payload.email);
            localStorage.setItem("username", payload.username);
            return { ...state, ...payload, loggedIn: true };
        });
    },
});

const selectAuth = (state: { auth: Auth }) => state.auth;

export { authSlice, selectAuth };