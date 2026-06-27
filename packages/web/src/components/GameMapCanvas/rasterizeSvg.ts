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
    const blob = new Blob([svg], { type: "image/svg+xml;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const image = new Image();

    image.onload = () => {
      const canvas = document.createElement("canvas");
      canvas.width = Math.max(1, Math.round(width));
      canvas.height = Math.max(1, Math.round(height));
      const context = canvas.getContext("2d");
      if (!context) {
        URL.revokeObjectURL(url);
        reject(new Error("Could not acquire a 2D canvas context"));
        return;
      }
      context.drawImage(image, 0, 0, canvas.width, canvas.height);
      URL.revokeObjectURL(url);
      canvas.toBlob((png) => {
        if (!png) {
          reject(new Error("Failed to rasterise base map to PNG"));
          return;
        }
        resolve(URL.createObjectURL(png));
      }, "image/png");
    };

    image.onerror = () => {
      URL.revokeObjectURL(url);
      reject(new Error("Base map SVG failed to load for rasterisation"));
    };

    image.src = url;
  });
