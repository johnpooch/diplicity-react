import { PayloadAction, createSlice } from "@reduxjs/toolkit";

type Order = {
    source?: string;
    type?: string;
    target?: string;
    aux?: string;
}

const initialState: Order = {};

const orderSlice = createSlice({
    name: "order",
    initialState,
    reducers: (creator) => ({
        updateOrder: creator.reducer((state, action: PayloadAction<string>) => {
            if (!state.source) {
                state.source = action.payload;
            } else if (!state.type) {
                state.type = action.payload;
            } else if ((state.type === "Support" || state.type === "Convoy") && !state.aux) {
                state.aux = action.payload;
            } else {
                state.target = action.payload;
            }
        }),
        resetOrder: creator.reducer(() => {
            return initialState;
        }),
    }),
    selectors: {
        selectOrder: (state) => state,
        selectStep: (state): "source" | "type" | "aux" | "target" => {
            if (!state.source) {
                return "source";
            }
            if (!state.type) {
                return "type";
            }
            if (state.type === "Support" || state.type === "Convoy") {
                if (!state.aux) {
                    return "aux";
                }
            }
            return "target";
        },
        selectIsComplete: (state) => {
            if (!state.type) {
                return false;
            }
            if (state.type === "Hold" || state.type === "Build" || state.type === "Disband") {
                return !!state.source;
            }
            if (state.type === "Move") {
                return !!state.source && !!state.target;
            }
            if (state.type === "Support" || state.type === "Convoy") {
                return !!state.source && !!state.aux && !!state.target;
            }
            return false;
        }
    }
});

export { orderSlice };