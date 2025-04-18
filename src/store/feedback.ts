import {
    createSlice,
    PayloadAction,
} from "@reduxjs/toolkit";
import { RootState } from "./store";
import { service } from "./service";

type Feedback = {
    severity?: "success" | "error" | "warning" | "info";
    message?: string;
};

const feedbackSlice = createSlice({
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
    extraReducers: (builder) => {
        builder.addMatcher(service.endpoints.authLoginCreate.matchFulfilled,
            (_, action) => {
                return {
                    severity: "success",
                    message: `Logged in as ${action.payload.username}`,
                };
            }
        )
    },
});

const feedbackActions = {
    clearFeedback: feedbackSlice.actions.clearFeedback,
    setFeedback: feedbackSlice.actions.setFeedback,
};

const selectFeedback = (state: RootState) => state.feedback;

export { selectFeedback, feedbackSlice, feedbackActions };