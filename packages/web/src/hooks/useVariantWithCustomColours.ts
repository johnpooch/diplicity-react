import { useMemo } from "react";
import { useCustomNationColours } from "./useCustomNationColours";
import type { Variant } from "@/api/generated/endpoints";

export function useVariantWithCustomColours(
  variants: Variant[] | undefined,
  variantId: string | undefined,
): Variant | undefined {
  const applyCustomColours = useCustomNationColours();
  return useMemo(() => {
    const raw = variants?.find(v => v.id === variantId);
    return raw ? { ...raw, nations: applyCustomColours(raw.nations) } : undefined;
  }, [variants, variantId, applyCustomColours]);
}
