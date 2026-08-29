import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { downscaleImage } from "./downscaleImage";

const createFile = (type: string) =>
  new File(["original"], "photo.jpg", { type });

const stubBitmap = (width: number, height: number) => {
  const close = vi.fn();
  vi.stubGlobal(
    "createImageBitmap",
    vi.fn(async () => ({ width, height, close }))
  );
  return close;
};

const stubCanvas = () => {
  const drawImage = vi.fn();
  let size: { width: number; height: number } | undefined;
  vi.spyOn(HTMLCanvasElement.prototype, "getContext").mockImplementation(
    function (this: HTMLCanvasElement) {
      size = { width: this.width, height: this.height };
      return { drawImage, imageSmoothingQuality: "low" } as never;
    }
  );
  vi.spyOn(HTMLCanvasElement.prototype, "toBlob").mockImplementation(
    (callback, type) => callback(new Blob(["downscaled"], { type }))
  );
  return {
    drawImage,
    get size() {
      return size;
    },
  };
};

describe("downscaleImage", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("downscales a large image to the bounded dimension", async () => {
    stubBitmap(4000, 3000);
    const canvas = stubCanvas();
    const file = createFile("image/jpeg");

    const result = await downscaleImage(file);

    expect(canvas.size).toEqual({ width: 512, height: 384 });
    expect(canvas.drawImage).toHaveBeenCalled();
    expect(result).not.toBe(file);
    expect(result.name).toBe("photo.jpg");
    expect(result.type).toBe("image/jpeg");
  });

  it("bounds the taller side of a portrait image", async () => {
    stubBitmap(1500, 3000);
    const canvas = stubCanvas();

    await downscaleImage(createFile("image/jpeg"));

    expect(canvas.size).toEqual({ width: 256, height: 512 });
  });

  it("releases the decoded bitmap", async () => {
    const close = stubBitmap(4000, 3000);
    stubCanvas();

    await downscaleImage(createFile("image/jpeg"));

    expect(close).toHaveBeenCalled();
  });

  it("returns the original file when it is already within bounds", async () => {
    stubBitmap(256, 256);
    const canvas = stubCanvas();
    const file = createFile("image/png");

    expect(await downscaleImage(file)).toBe(file);
    expect(canvas.size).toBeUndefined();
  });

  it("returns the original file for a type the server does not accept", async () => {
    stubBitmap(4000, 3000);
    const file = createFile("image/heic");

    expect(await downscaleImage(file)).toBe(file);
  });

  it("returns the original file when the browser cannot decode images", async () => {
    const file = createFile("image/jpeg");

    expect(await downscaleImage(file)).toBe(file);
  });

  it("returns the original file when decoding fails", async () => {
    vi.stubGlobal(
      "createImageBitmap",
      vi.fn(async () => {
        throw new Error("decode failed");
      })
    );
    const file = createFile("image/jpeg");

    expect(await downscaleImage(file)).toBe(file);
  });

  it("returns the original file when encoding yields nothing", async () => {
    stubBitmap(4000, 3000);
    stubCanvas();
    vi.spyOn(HTMLCanvasElement.prototype, "toBlob").mockImplementation(
      callback => callback(null)
    );
    const file = createFile("image/jpeg");

    expect(await downscaleImage(file)).toBe(file);
  });
});
