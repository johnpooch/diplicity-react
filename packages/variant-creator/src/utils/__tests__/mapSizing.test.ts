import { describe, it, expect } from "vitest";
import { calculateMapMaxHeight } from "../mapSizing";

describe("calculateMapMaxHeight", () => {
  it("returns higher maxHeight for portrait maps", () => {
    // hundred variant: 662x1082, ratio ~0.61
    const result = calculateMapMaxHeight({ width: 662, height: 1082 });
    expect(result).toBe("66vh");
  });

  it("returns 50vh for square maps", () => {
    const result = calculateMapMaxHeight({ width: 100, height: 100 });
    expect(result).toBe("50vh");
  });

  it("returns lower maxHeight for landscape maps", () => {
    // test-map: 800x600, ratio ~1.33
    const result = calculateMapMaxHeight({ width: 800, height: 600 });
    expect(result).toBe("43vh");
  });

  it("caps at 40vh for very wide maps", () => {
    // ratio 2.0
    const result = calculateMapMaxHeight({ width: 200, height: 100 });
    expect(result).toBe("40vh");
  });

  it("caps at 70vh for very tall maps", () => {
    // ratio 0.25
    const result = calculateMapMaxHeight({ width: 100, height: 400 });
    expect(result).toBe("70vh");
  });

  it("handles slightly landscape maps", () => {
    // ratio 1.2
    const result = calculateMapMaxHeight({ width: 120, height: 100 });
    expect(result).toBe("46vh");
  });

  it("handles slightly portrait maps", () => {
    // ratio 0.8
    const result = calculateMapMaxHeight({ width: 80, height: 100 });
    expect(result).toBe("58vh");
  });
});
