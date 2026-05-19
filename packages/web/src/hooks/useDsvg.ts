import { useQuery } from "@tanstack/react-query";
import axiosInstance from "../api/axiosInstance";

const fetchDsvg = async (svgUrl: string): Promise<string> => {
  const response = await axiosInstance.get<string>(svgUrl, {
    responseType: "text",
    transformResponse: (data) => data,
  });
  return response.data;
};

export const useDsvg = (svgUrl: string | null | undefined) => {
  return useQuery({
    queryKey: ["dsvg", svgUrl],
    queryFn: () => fetchDsvg(svgUrl as string),
    enabled: !!svgUrl,
    staleTime: Infinity,
    gcTime: Infinity,
  });
};
