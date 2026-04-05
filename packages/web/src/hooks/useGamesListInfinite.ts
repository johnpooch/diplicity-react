import { useSuspenseInfiniteQuery } from "@tanstack/react-query";
import {
  gamesList,
  getGamesListQueryKey,
} from "@/api/generated/endpoints";
import type { GamesListParams } from "@/api/generated/endpoints";

const getNextPageParam = (lastPage: Awaited<ReturnType<typeof gamesList>>) => {
  if (!lastPage.next) return undefined;
  const url = new URL(lastPage.next);
  const page = url.searchParams.get("page");
  return page ? Number(page) : undefined;
};

export const useGamesListInfinite = (params?: GamesListParams) => {
  return useSuspenseInfiniteQuery({
    queryKey: [...getGamesListQueryKey(params), "infinite"],
    queryFn: ({ pageParam }) => gamesList({ ...params, page: pageParam }),
    initialPageParam: 1,
    getNextPageParam,
  });
};
