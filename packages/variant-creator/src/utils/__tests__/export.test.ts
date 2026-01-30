import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { downloadVariantJson, generateFilename } from "../export";
import type { VariantDefinition } from "@/types/variant";

const createMockVariant = (
  overrides: Partial<VariantDefinition> = {}
): VariantDefinition => ({
  name: "",
  description: "",
  author: "",
  version: "1.0.0",
  soloVictorySCCount: 0,
  nations: [],
  provinces: [],
  namedCoasts: [],
  decorativeElements: [],
  dimensions: { width: 1000, height: 800 },
  textElements: [],
  ...overrides,
});

describe("generateFilename", () => {
  it("returns variant.json when name is empty", () => {
    expect(generateFilename("")).toBe("variant.json");
  });

  it("returns variant.json when name is only whitespace", () => {
    expect(generateFilename("   ")).toBe("variant.json");
  });

  it("converts name to lowercase", () => {
    expect(generateFilename("MyVariant")).toBe("myvariant.json");
  });

  it("replaces spaces with hyphens", () => {
    expect(generateFilename("My Custom Variant")).toBe("my-custom-variant.json");
  });

  it("replaces multiple spaces with single hyphen", () => {
    expect(generateFilename("My   Variant")).toBe("my-variant.json");
  });

  it("handles mixed case and spaces", () => {
    expect(generateFilename("The Great War")).toBe("the-great-war.json");
  });
});

describe("downloadVariantJson", () => {
  let createObjectURLMock: ReturnType<typeof vi.fn>;
  let revokeObjectURLMock: ReturnType<typeof vi.fn>;
  let clickMock: ReturnType<typeof vi.fn>;
  let createdAnchor: HTMLAnchorElement | null = null;

  beforeEach(() => {
    createObjectURLMock = vi.fn().mockReturnValue("blob:test-url");
    revokeObjectURLMock = vi.fn();
    clickMock = vi.fn();

    global.URL.createObjectURL = createObjectURLMock;
    global.URL.revokeObjectURL = revokeObjectURLMock;

    vi.spyOn(document, "createElement").mockImplementation((tag: string) => {
      if (tag === "a") {
        createdAnchor = {
          href: "",
          download: "",
          click: clickMock,
        } as unknown as HTMLAnchorElement;
        return createdAnchor;
      }
      return document.createElement(tag);
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
    createdAnchor = null;
  });

  it("creates a blob with pretty-printed JSON", () => {
    const variant = createMockVariant({ name: "Test" });
    downloadVariantJson(variant);

    expect(createObjectURLMock).toHaveBeenCalledTimes(1);
    const blob = createObjectURLMock.mock.calls[0][0] as Blob;
    expect(blob.type).toBe("application/json");
  });

  it("triggers download with correct filename for named variant", () => {
    const variant = createMockVariant({ name: "My Variant" });
    downloadVariantJson(variant);

    expect(createdAnchor?.download).toBe("my-variant.json");
    expect(clickMock).toHaveBeenCalled();
  });

  it("uses default filename for unnamed variant", () => {
    const variant = createMockVariant({ name: "" });
    downloadVariantJson(variant);

    expect(createdAnchor?.download).toBe("variant.json");
  });

  it("revokes object URL after download", () => {
    const variant = createMockVariant();
    downloadVariantJson(variant);

    expect(revokeObjectURLMock).toHaveBeenCalledWith("blob:test-url");
  });

  it("sets correct href on anchor element", () => {
    const variant = createMockVariant();
    downloadVariantJson(variant);

    expect(createdAnchor?.href).toBe("blob:test-url");
  });
});
