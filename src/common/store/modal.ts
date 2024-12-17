import {
    createSlice,
    PayloadAction,
} from "@reduxjs/toolkit";
import { RootState } from "./store";

type Modal = {
    view?: "player-info";
    id?: string;
};

export const modalSlice = createSlice({
    name: "modal",
    initialState: {} as Modal,
    reducers: {
        clearModal: () => {
            return {};
        },
        setModal: (_, action: PayloadAction<Modal>) => {
            return action.payload;
        },
    },
    extraReducers: () => {
    },
});

export const modalActions = {
    clearModal: modalSlice.actions.clearModal,
    setModal: modalSlice.actions.setModal,
};

export const selectModal = (state: RootState) => state.modal;