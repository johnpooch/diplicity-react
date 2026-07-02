import React, { Suspense } from "react";
import { Link, useSearchParams } from "react-router";
import { Bot } from "lucide-react";

import { ScreenContainer } from "@/components/ui/screen-container";
import { ScreenHeader } from "@/components/ui/screen-header";
import { Badge } from "@/components/ui/badge";
import {
  Item,
  ItemContent,
  ItemTitle,
  ItemDescription,
  ItemGroup,
  ItemSeparator,
} from "@/components/ui/item";
import { Notice } from "@/components/Notice";
import { QueryErrorBoundary } from "@/components/QueryErrorBoundary";
import { useLlmCallsListSuspense } from "@/api/generated/endpoints";
import type { LLMCallSummary } from "@/api/generated/endpoints";

const formatTimestamp = (value: string): string =>
  new Date(value).toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });

const buildBottomLine = (call: LLMCallSummary, showGame: boolean): string => {
  const parts = [formatTimestamp(call.createdAt)];
  if (showGame && call.gameId) {
    parts.push(call.gameId);
  }
  return parts.join(" · ");
};

const LLMCallsList: React.FC = () => {
  const [searchParams] = useSearchParams();
  const gameId = searchParams.get("game") ?? undefined;
  const { data: calls } = useLlmCallsListSuspense(
    gameId ? { game: gameId } : undefined
  );

  if (calls.length === 0) {
    return (
      <Notice
        icon={Bot}
        title="No LLM calls"
        message={
          gameId
            ? "No LLM calls have been recorded for this game yet."
            : "No LLM calls have been recorded yet."
        }
      />
    );
  }

  return (
    <ItemGroup>
      {calls.map(call => (
        <React.Fragment key={call.id}>
          <Item asChild size="sm" className="py-2">
            <Link
              to={`/llm-calls/${call.id}`}
              className="text-foreground no-underline"
            >
              <ItemContent className="gap-0.5">
                <ItemTitle>
                  <Badge variant="outline">{call.stage}</Badge>
                  {call.nation ?? "Unknown"}
                  <span className="font-normal text-muted-foreground">
                    {call.phaseName}
                  </span>
                  {call.status === "error" && (
                    <Badge variant="destructive">error</Badge>
                  )}
                </ItemTitle>
                <ItemDescription>
                  {buildBottomLine(call, !gameId)}
                </ItemDescription>
              </ItemContent>
            </Link>
          </Item>
          <ItemSeparator />
        </React.Fragment>
      ))}
    </ItemGroup>
  );
};

const LLMCallsListScreen: React.FC = () => (
  <ScreenContainer>
    <ScreenHeader title="LLM Calls" />
    <QueryErrorBoundary>
      <Suspense fallback={<div></div>}>
        <LLMCallsList />
      </Suspense>
    </QueryErrorBoundary>
  </ScreenContainer>
);

export { LLMCallsListScreen };
