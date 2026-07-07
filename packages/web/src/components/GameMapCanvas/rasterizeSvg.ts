// An SVG with a viewBox but no width/height has no intrinsic size, so a
// browser can fall back to a default concrete size (300×150) and letterbox
// the content when it's drawn as an <image>. Stamping the root tag with the
// same width/height the canvas will use keeps the rasterised base aligned
// with the vector overlays, which Leaflet positions from the true viewBox.
export const injectSvgDimensions = (
  svg: string,
  width: number,
  height: number
): string => svg.replace("<svg ", `<svg width="${width}" height="${height}" `);

// Ceiling on the rasterised base's pixel area. Variants with very large
// viewBoxes (e.g. Cold War 1961 at 4000x4000 = 16 MP) can exceed the canvas
// area limit on mobile Safari/iOS WebKit and memory-constrained devices,
// causing drawImage/toBlob to fail silently. The raster is only a backdrop
// image positioned by Leaflet from the true viewBox, so downscaling it is
// safe — it only slightly softens the base landmass at maximum zoom.
export const MAX_RASTER_PIXELS = 4_000_000;

export const computeRasterDimensions = (
  width: number,
  height: number,
  maxPixels: number = MAX_RASTER_PIXELS
): { width: number; height: number } => {
  const scale = Math.min(1, Math.sqrt(maxPixels / (width * height)));
  return { width: width * scale, height: height * scale };
};

// Rasterises an SVG string to a PNG object URL once. Per the map re-architecture
// proposal, the static base is rasterised a single time and thereafter only
// moved by the camera, so the ~17k path commands are never repainted per frame.
// The board is drawn at its native viewBox resolution, capped to a pixel-area
// budget (the accepted "soft base map at 4× zoom" trade).
export const rasterizeSvg = (
  svg: string,
  width: number,
  height: number
): Promise<string> =>
  new Promise((resolve, reject) => {
    const rasterDimensions = computeRasterDimensions(width, height);
    const sizedSvg = injectSvgDimensions(
      svg,
      rasterDimensions.width,
      rasterDimensions.height
    );
    const blob = new Blob([sizedSvg], { type: "image/svg+xml;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const image = new Image();

    image.onload = async () => {
      try {
        // Decoding is async and cache-dependent; waiting for it to settle
        // before drawImage avoids racing a partially decoded frame under
        // rapid successive map loads.
        if (image.decode) {
          await image.decode();
        }
        const canvas = document.createElement("canvas");
        canvas.width = Math.max(1, Math.round(rasterDimensions.width));
        canvas.height = Math.max(1, Math.round(rasterDimensions.height));
        const context = canvas.getContext("2d");
        if (!context) {
          throw new Error("Could not acquire a 2D canvas context");
        }
        context.drawImage(image, 0, 0, canvas.width, canvas.height);
        canvas.toBlob((png) => {
          if (!png) {
            reject(new Error("Failed to rasterise base map to PNG"));
            return;
          }
          resolve(URL.createObjectURL(png));
        }, "image/png");
      } catch (error) {
        reject(error);
      } finally {
        URL.revokeObjectURL(url);
      }
    };

    image.onerror = () => {
      URL.revokeObjectURL(url);
      reject(new Error("Base map SVG failed to load for rasterisation"));
    };

    image.src = url;
  });
