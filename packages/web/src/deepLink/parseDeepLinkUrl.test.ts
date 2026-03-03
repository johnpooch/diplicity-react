import { describe, it, expect } from "vitest";
import { parseDeepLinkUrl } from "./parseDeepLinkUrl";

describe("parseDeepLinkUrl", () => {
  describe("custom scheme (diplicity://)", () => {
    it("parses a game deep link", () => {
      expect(parseDeepLinkUrl("diplicity://game/123/phase/456/orders")).toBe(
        "/game/123/phase/456/orders"
      );
    });

    it("parses a root path", () => {
      expect(parseDeepLinkUrl("diplicity://")).toBe("/");
    });

    it("parses a path with query params", () => {
      expect(parseDeepLinkUrl("diplicity://find-games?sort=newest")).toBe(
        "/find-games?sort=newest"
      );
    });

    it("handles leading slashes", () => {
      expect(parseDeepLinkUrl("diplicity:///game/123")).toBe("/game/123");
    });
  });

  describe("universal links (https://diplicity.com)", () => {
    it("parses a game link", () => {
      expect(
        parseDeepLinkUrl("https://diplicity.com/game/123/phase/456/orders")
      ).toBe("/game/123/phase/456/orders");
    });

    it("parses root path", () => {
      expect(parseDeepLinkUrl("https://diplicity.com/")).toBe("/");
    });

    it("parses with query params and hash", () => {
      expect(
        parseDeepLinkUrl("https://diplicity.com/profile?tab=stats#section")
      ).toBe("/profile?tab=stats#section");
    });

    it("parses www subdomain", () => {
      expect(parseDeepLinkUrl("https://www.diplicity.com/game/123")).toBe(
        "/game/123"
      );
    });

    it("parses http scheme", () => {
      expect(parseDeepLinkUrl("http://diplicity.com/game/123")).toBe(
        "/game/123"
      );
    });
  });

  describe("unknown domains", () => {
    it("returns null for unknown domain", () => {
      expect(parseDeepLinkUrl("https://evil.com/game/123")).toBeNull();
    });

    it("returns null for subdomain that is not www", () => {
      expect(parseDeepLinkUrl("https://api.diplicity.com/game/123")).toBeNull();
    });
  });

  describe("invalid URLs", () => {
    it("returns null for empty string", () => {
      expect(parseDeepLinkUrl("")).toBeNull();
    });

    it("returns null for garbage", () => {
      expect(parseDeepLinkUrl("not a url")).toBeNull();
    });
  });
});
