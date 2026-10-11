import { useEffect, useMemo, useRef } from "react";
import { useSuspenseInfiniteQuery } from "@tanstack/react-query";
import {
  gamesChannelsMessagesRetrieve,
  getGamesChannelsMessagesRetrieveQueryKey,
} from "@/api/generated/endpoints";
import type {
  ChannelMessage,
  ChannelMessagePage,
  GamesChannelsMessagesRetrieveParams,
} from "@/api/generated/endpoints";

const messageIds = (pages: readonly ChannelMessagePage[]) =>
  pages.flatMap(page => page.results.map(message => message.id));

const oldestPage = (pages: readonly ChannelMessagePage[]) =>
  pages.find(page => page.results.length > 0);

export const useChannelMessages = (
  gameId: string,
  channelId: number,
  latestMessageId: number | null
) => {
  const {
    data,
    fetchNextPage,
    fetchPreviousPage,
    isFetching,
    isFetchingPreviousPage,
    isFetchPreviousPageError,
  } = useSuspenseInfiniteQuery({
    queryKey: [
      ...getGamesChannelsMessagesRetrieveQueryKey(gameId, channelId),
      "infinite",
    ],
    queryFn: ({ pageParam, signal }) =>
      gamesChannelsMessagesRetrieve(gameId, channelId, pageParam, signal),
    initialPageParam: {} as GamesChannelsMessagesRetrieveParams,
    getPreviousPageParam: (_firstPage, pages) =>
      oldestPage(pages)?.hasOlder
        ? { before: Math.min(...messageIds(pages)) }
        : undefined,
    getNextPageParam: (_lastPage, pages): GamesChannelsMessagesRetrieveParams => {
      const ids = messageIds(pages);
      return ids.length > 0 ? { after: Math.max(...ids) } : {};
    },
    staleTime: Infinity,
    gcTime: 0,
  });

  const messages = useMemo(() => {
    const byId = new Map<number, ChannelMessage>();
    data.pages.forEach(page =>
      page.results.forEach(message => byId.set(message.id, message))
    );
    return [...byId.values()].sort(
      (a, b) => Date.parse(a.createdAt) - Date.parse(b.createdAt) || a.id - b.id
    );
  }, [data.pages]);

  const ids = messageIds(data.pages);
  const newestLoadedId = ids.length > 0 ? Math.max(...ids) : null;
  const behind =
    latestMessageId !== null &&
    (newestLoadedId === null || latestMessageId > newestLoadedId);
  const hasNewer = data.pages[data.pages.length - 1].hasNewer || behind;
  const boundary = `${gameId}/${channelId}/${newestLoadedId}/${latestMessageId}`;
  const requestedBoundaryRef = useRef<string | null>(null);

  useEffect(() => {
    if (!hasNewer || isFetching) return;
    if (requestedBoundaryRef.current === boundary) return;
    requestedBoundaryRef.current = boundary;
    fetchNextPage();
  }, [hasNewer, isFetching, boundary, fetchNextPage]);

  return {
    messages,
    hasOlder: oldestPage(data.pages)?.hasOlder ?? false,
    fetchOlder: fetchPreviousPage,
    isFetchingOlder: isFetchingPreviousPage,
    isFetchOlderError: isFetchPreviousPageError,
  };
};
