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

// Rasterises an SVG string to a PNG object URL once. Per the map re-architecture
// proposal, the static base is rasterised a single time and thereafter only
// moved by the camera, so the ~17k path commands are never repainted per frame.
// The board is drawn at its native viewBox resolution (the accepted "soft base
// map at 4× zoom" trade).
export const rasterizeSvg = (
  svg: string,
  width: number,
  height: number
): Promise<string> =>
  new Promise((resolve, reject) => {
    const sizedSvg = injectSvgDimensions(svg, width, height);
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
        canvas.width = Math.max(1, Math.round(width));
        canvas.height = Math.max(1, Math.round(height));
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
