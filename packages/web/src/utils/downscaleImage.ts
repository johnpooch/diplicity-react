const MAX_DIMENSION = 512;
const IMAGE_QUALITY = 0.9;
const DOWNSCALABLE_TYPES = ["image/jpeg", "image/png", "image/webp"];

export const downscaleImage = async (file: File): Promise<File> => {
  if (!DOWNSCALABLE_TYPES.includes(file.type)) return file;
  if (typeof createImageBitmap !== "function") return file;

  let bitmap: ImageBitmap;
  try {
    bitmap = await createImageBitmap(file, { imageOrientation: "from-image" });
  } catch {
    return file;
  }

  const scale = MAX_DIMENSION / Math.max(bitmap.width, bitmap.height);
  if (scale >= 1) {
    bitmap.close();
    return file;
  }

  const canvas = document.createElement("canvas");
  canvas.width = Math.round(bitmap.width * scale);
  canvas.height = Math.round(bitmap.height * scale);
  const context = canvas.getContext("2d");
  if (!context) {
    bitmap.close();
    return file;
  }
  context.imageSmoothingQuality = "high";
  context.drawImage(bitmap, 0, 0, canvas.width, canvas.height);
  bitmap.close();

  const blob = await new Promise<Blob | null>(resolve =>
    canvas.toBlob(resolve, file.type, IMAGE_QUALITY)
  );
  if (!blob) return file;

  return new File([blob], file.name, { type: blob.type });
};
