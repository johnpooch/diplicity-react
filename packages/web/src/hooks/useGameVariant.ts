import {
  useVariantsListSuspense,
  useVariantsRetrieve,
  type Variant,
} from "@/api/generated/endpoints";

export const useGameVariant = (game: {
  variantId: string;
}): Variant | undefined => {
  const { data: variants } = useVariantsListSuspense();
  const published = variants.find(v => v.id === game.variantId);
  const { data: fetched } = useVariantsRetrieve(game.variantId, {
    query: { enabled: !published },
  });
  return published ?? fetched;
};
