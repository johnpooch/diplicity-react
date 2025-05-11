import { isUnauthorized } from "../matchers";
import { PayloadAction } from "@reduxjs/toolkit";

describe("isUnauthorized", () => {
    it("should return true for action with status 401", () => {
        const action: PayloadAction<{ status: 401 }> = {
            type: "test",
            payload: { status: 401 }
        };
        expect(isUnauthorized(action)).toBe(true);
    });

    it("should return false for action with different status", () => {
        const action: PayloadAction<{ status: 403 }> = {
            type: "test",
            payload: { status: 403 }
        };
        expect(isUnauthorized(action)).toBe(false);
    });

    it("should return false for action with no status", () => {
        const action: PayloadAction<{ message: string }> = {
            type: "test",
            payload: { message: "Unauthorized" }
        };
        expect(isUnauthorized(action)).toBe(false);
    });

    it("should return false for action with non-object payload", () => {
        const action: PayloadAction<string> = {
            type: "test",
            payload: "Unauthorized"
        };
        expect(isUnauthorized(action)).toBe(false);
    });

    it("should return false for action with null payload", () => {
        const action: PayloadAction<null> = {
            type: "test",
            payload: null
        };
        expect(isUnauthorized(action)).toBe(false);
    });
});
