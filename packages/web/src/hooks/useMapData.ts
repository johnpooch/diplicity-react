import { useQuery } from "@tanstack/react-query";

export type MapData = {
  width: number;
  height: number;
  provinces: Array<{
    id: string;
    path: { d: string };
    center: { x: number; y: number };
    supplyCenter?: { x: number; y: number };
    text?: Array<{
      point: { x: number; y: number };
      value: string;
      styles: React.CSSProperties;
      transform?: string;
    }>;
  }>;
  backgroundElements: Array<{
    d: string;
    styles: {
      fill: string;
      stroke: string;
      strokeWidth: number;
    };
  }>;
  borders: Array<{
    id: string;
    d: string;
  }>;
  impassableProvinces: Array<{
    id: string;
    d: string;
  }>;
};

const isJsonResponse = (response: Response): boolean => {
  const contentType = response.headers.get("content-type");
  return contentType?.includes("application/json") ?? false;
};

const fetchMapData = async (variantId: string): Promise<MapData> => {
  const response = await fetch(`/maps/${variantId}.json`);
  if (!response.ok || !isJsonResponse(response)) {
    // Fall back to classical if the variant map doesn't exist
    const fallbackResponse = await fetch("/maps/classical.json");
    if (!fallbackResponse.ok || !isJsonResponse(fallbackResponse)) {
      throw new Error("Failed to load map data");
    }
    return fallbackResponse.json();
  }
  return response.json();
};

export const useMapData = (variantId: string) => {
  return useQuery({
    queryKey: ["mapData", variantId],
    queryFn: () => fetchMapData(variantId),
    staleTime: Infinity,
    gcTime: Infinity,
  });
};
