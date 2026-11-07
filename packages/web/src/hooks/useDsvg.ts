import { useQuery } from "@tanstack/react-query";
import axiosInstance from "../api/axiosInstance";
import { parseDsvg, type ParsedDsvg } from "../components/InteractiveMap/dsvgParser";

const fetchDsvg = async (svgUrl: string): Promise<ParsedDsvg> => {
  const response = await axiosInstance.get<string>(svgUrl, {
    responseType: "text",
    transformResponse: (data) => data,
  });
  return parseDsvg(response.data);
};

export const useDsvg = (svgUrl: string | null | undefined, enabled = true) => {
  return useQuery({
    queryKey: ["dsvg", svgUrl],
    queryFn: () => fetchDsvg(svgUrl as string),
    enabled: !!svgUrl && enabled,
    staleTime: Infinity,
    gcTime: Infinity,
  });
};
