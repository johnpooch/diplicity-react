import { describe, it, expect } from "vitest";
import { suggestId, validateProvinceId, isUniqueId } from "../idSuggestion";

describe("suggestId", () => {
  it("returns first 3 letters for single word", () => {
    expect(suggestId("Berlin")).toBe("ber");
  });

  it("returns lowercase", () => {
    expect(suggestId("MUNICH")).toBe("mun");
  });

  it("returns initials for multiple words with 3+ words", () => {
    expect(suggestId("North Atlantic Ocean")).toBe("nao");
  });

  it("returns 2 initials + extra letter for 2-word names", () => {
    expect(suggestId("North Sea")).toBe("nse");
  });

  it("trims whitespace", () => {
    expect(suggestId("  Berlin  ")).toBe("ber");
  });

  it("returns empty string for empty input", () => {
    expect(suggestId("")).toBe("");
  });

  it("returns empty string for whitespace-only input", () => {
    expect(suggestId("   ")).toBe("");
  });

  it("handles single character words", () => {
    expect(suggestId("A B C")).toBe("abc");
  });

  it("handles mixed case with 2 words", () => {
    expect(suggestId("St. Petersburg")).toBe("spe");
  });
});

describe("validateProvinceId", () => {
  it("returns valid for 3 lowercase letters", () => {
    expect(validateProvinceId("ber")).toEqual({ valid: true });
  });

  it("returns invalid for empty string", () => {
    const result = validateProvinceId("");
    expect(result.valid).toBe(false);
    expect(result.error).toBe("ID is required");
  });

  it("returns invalid for less than 3 characters", () => {
    const result = validateProvinceId("be");
    expect(result.valid).toBe(false);
    expect(result.error).toBe("ID must be exactly 3 characters");
  });

  it("returns invalid for more than 3 characters", () => {
    const result = validateProvinceId("berl");
    expect(result.valid).toBe(false);
    expect(result.error).toBe("ID must be exactly 3 characters");
  });

  it("returns invalid for uppercase letters", () => {
    const result = validateProvinceId("BER");
    expect(result.valid).toBe(false);
    expect(result.error).toBe("ID must be 3 lowercase letters");
  });

  it("returns invalid for numbers", () => {
    const result = validateProvinceId("be1");
    expect(result.valid).toBe(false);
    expect(result.error).toBe("ID must be 3 lowercase letters");
  });

  it("returns invalid for special characters", () => {
    const result = validateProvinceId("be-");
    expect(result.valid).toBe(false);
    expect(result.error).toBe("ID must be 3 lowercase letters");
  });
});

describe("isUniqueId", () => {
  it("returns true when ID is not in existing list", () => {
    expect(isUniqueId("ber", ["mun", "kie", "pru"])).toBe(true);
  });

  it("returns false when ID is in existing list", () => {
    expect(isUniqueId("ber", ["ber", "mun", "kie"])).toBe(false);
  });

  it("returns true when ID matches currentId (self-reference)", () => {
    expect(isUniqueId("ber", ["ber", "mun", "kie"], "ber")).toBe(true);
  });

  it("returns false when ID matches another entry besides currentId", () => {
    expect(isUniqueId("mun", ["ber", "mun", "kie"], "ber")).toBe(false);
  });

  it("returns true for empty existing list", () => {
    expect(isUniqueId("ber", [])).toBe(true);
  });
});
