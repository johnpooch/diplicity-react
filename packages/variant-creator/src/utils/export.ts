import type { VariantDefinition } from "@/types/variant";

export function downloadVariantJson(variant: VariantDefinition): void {
  const json = JSON.stringify(variant, null, 2);
  const blob = new Blob([json], { type: "application/json" });
  const url = URL.createObjectURL(blob);

  const filename = variant.name.trim()
    ? `${variant.name.toLowerCase().replace(/\s+/g, "-")}.json`
    : "variant.json";

  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();

  URL.revokeObjectURL(url);
}

export function generateFilename(variantName: string): string {
  const trimmed = variantName.trim();
  if (!trimmed) {
    return "variant.json";
  }
  return `${trimmed.toLowerCase().replace(/\s+/g, "-")}.json`;
}
