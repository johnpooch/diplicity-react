import { describe, test } from "vitest";
import { transformResolution } from "../util";

describe("transformResolution", () => {
    test("OK", () => {
        const resolution = "OK";
        const result = transformResolution(resolution);
        expect(result).toEqual({
            outcome: "Succeeded",
        });
    })
    test("ErrBounce:pie", () => {
        const resolution = "ErrBounce:pie";
        const result = transformResolution(resolution);
        expect(result).toEqual({
            outcome: "Bounced",
            by: "pie",
        });
    })
    test("ErrBounce:bul/ec", () => {
        const resolution = "ErrBounce:bul/ec";
        const result = transformResolution(resolution);
        expect(result).toEqual({
            outcome: "Bounced",
            by: "bul/ec",
        });
    })
    test("ErrSupportBroken:pie", () => {
        const resolution = "ErrSupportBroken:pie";
        const result = transformResolution(resolution);
        expect(result).toEqual({
            outcome: "Support broken",
            by: "pie",
        });
    })
    test("ErrInvalidSupporteeOrder", () => {
        const resolution = "ErrInvalidSupporteeOrder";
        const result = transformResolution(resolution);
        expect(result).toEqual({
            outcome: "Invalid order",
        });
    })
});
