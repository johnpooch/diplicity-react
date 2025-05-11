import {
    createSlice,
    PayloadAction,
} from "@reduxjs/toolkit";
import { RootState } from "./store";
import service from "./service";

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
    extraReducers: (builder) => {
        builder.addMatcher(
            service.endpoints.createGame.matchFulfilled,
            (_, action) => {
                return {
                    severity: "success",
                    message: `Game "${action.payload.Desc}" created successfully`,
                };
            }
        );
        builder.addMatcher(
            service.endpoints.createOrder.matchFulfilled,
            () => {
                return {
                    severity: "success",
                    message: `Order created successfully`,
                };
            }
        );
        builder.addMatcher(
            service.endpoints.updatePhaseState.matchFulfilled,
            (_, action) => {
                return {
                    severity: "success",
                    message: action.payload.Properties.ReadyToResolve ? `Orders confirmed` : `Orders unconfirmed`,
                };
            }
        );
        builder.addMatcher(
            service.endpoints.joinGame.matchFulfilled,
            () => {
                return {
                    severity: "success",
                    message: `Game joined successfully`,
                };
            }
        );
        builder.addMatcher(
            service.endpoints.leaveGame.matchFulfilled,
            () => {
                return {
                    severity: "success",
                    message: `Game left successfully`,
                };
            }
        );
    },
});

export const feedbackActions = {
    clearFeedback: feedbackSlice.actions.clearFeedback,
    setFeedback: feedbackSlice.actions.setFeedback,
};

export const selectFeedback = (state: RootState) => state.feedback;