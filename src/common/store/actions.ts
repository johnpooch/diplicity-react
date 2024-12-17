import { createAsyncThunk } from "@reduxjs/toolkit";
import service from "./service";

const initializeHomeScreen = createAsyncThunk("initializeHomeScreen", async (_, { dispatch }) => {
    await Promise.all([
        dispatch(service.endpoints.getRoot.initiate(undefined)),
        dispatch(service.endpoints.listVariants.initiate(undefined)),
        dispatch(service.endpoints.listGames.initiate({
            my: true,
            status: "Staging",
            mastered: false,
        })),
        dispatch(service.endpoints.listGames.initiate({
            my: true,
            status: "Started",
            mastered: false,
        })),
        dispatch(service.endpoints.listGames.initiate({
            my: true,
            status: "Finished",
            mastered: false,
        })),
    ]);
});

export { initializeHomeScreen };