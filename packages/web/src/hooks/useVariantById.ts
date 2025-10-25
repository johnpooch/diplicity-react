import { useRouteLoaderData } from "react-router";
import { VariantRead } from "../store";

export const useVariantById = (variantId: string): VariantRead | undefined => {
  const variants = useRouteLoaderData("root") as VariantRead[] | undefined;

  if (!variants) {
    return undefined;
  }

  return variants.find(variant => variant.id === variantId);
};
