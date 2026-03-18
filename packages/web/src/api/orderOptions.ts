import { useQuery } from "@tanstack/react-query";
import { customInstance } from "./axiosInstance";
import type { OrderOption, FieldName } from "../utils/deriveWizardStep";

interface OrderOptionsResponse {
  orders: OrderOption[];
  fieldOrder: Record<string, FieldName[]>;
}

function gameOrderOptionsRetrieve(gameId: string, signal?: AbortSignal) {
  return customInstance<OrderOptionsResponse>({
    url: `/api/game/${gameId}/options/`,
    method: "GET",
    signal,
  });
}

function getGameOrderOptionsRetrieveQueryKey(gameId: string) {
  return [`/api/game/${gameId}/options/`] as const;
}

function useGameOrderOptionsRetrieve(gameId: string) {
  return useQuery({
    queryKey: getGameOrderOptionsRetrieveQueryKey(gameId),
    queryFn: ({ signal }) => gameOrderOptionsRetrieve(gameId, signal),
    enabled: !!gameId,
  });
}

export {
  useGameOrderOptionsRetrieve,
  getGameOrderOptionsRetrieveQueryKey,
  gameOrderOptionsRetrieve,
};
export type { OrderOptionsResponse };
