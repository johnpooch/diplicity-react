import {
    createSlice,
    PayloadAction,
} from "@reduxjs/toolkit";
import { RootState } from "./store";

type Feedback = {
    severity?: "success" | "error" | "warning" | "info";
    message?: string;
};

export const feedbackSlice = createSlice({
    name: "feedback",
    initialState: {} as Feedback,
    reducers: {
        clearFeedback: () => {
            return {};
        },
        setFeedback: (_, action: PayloadAction<Feedback>) => {
            return action.payload;
        },
    },
    extraReducers: () => {
    },
});

export const feedbackActions = {
    clearFeedback: feedbackSlice.actions.clearFeedback,
};

export const selectFeedback = (state: RootState) => state.feedback;