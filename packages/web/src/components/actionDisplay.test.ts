import { describe, it, expect } from "vitest";

import { confirmationFor } from "./actionDisplay";

describe("confirmationFor withdraw", () => {
  it("warns about commitment in the first year", () => {
    const confirmation = confirmationFor("withdraw", undefined, {
      sandbox: false,
      isFirstYear: true,
    });

    expect(confirmation?.description).toBe(
      "Withdrawing in the first year impacts your commitment score negatively. Your seat will be offered to a replacement. You cannot rejoin this game."
    );
  });

  it("reassures about commitment after the first year", () => {
    const confirmation = confirmationFor("withdraw", undefined, {
      sandbox: false,
      isFirstYear: false,
    });

    expect(confirmation?.description).toBe(
      "Your commitment rating is not affected. You cannot rejoin this game."
    );
  });
});
