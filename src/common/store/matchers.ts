import { PayloadAction } from "@reduxjs/toolkit";

type UnauthorizedPayload = { status: 401 };

function isUnauthorized(action: PayloadAction<unknown>): action is PayloadAction<UnauthorizedPayload> {
    return Boolean(typeof action.payload === "object" && action.payload && "status" in action.payload && action.payload.status === 401);
}

export { isUnauthorized };