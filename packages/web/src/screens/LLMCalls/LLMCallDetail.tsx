import React, { Suspense } from "react";
import { useNavigate } from "react-router";
import { ArrowLeft } from "lucide-react";

import { ScreenContainer } from "@/components/ui/screen-container";
import { ScreenHeader } from "@/components/ui/screen-header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { QueryErrorBoundary } from "@/components/QueryErrorBoundary";
import { useRequiredParams } from "@/hooks";
import { useLlmCallsRetrieveSuspense } from "@/api/generated/endpoints";
import type { LLMCallDetail as LLMCallDetailType } from "@/api/generated/endpoints";

const MetaRow: React.FC<{ label: string; value: React.ReactNode }> = ({
  label,
  value,
}) => (
  <div className="flex gap-2 text-sm">
    <span className="w-32 shrink-0 text-muted-foreground">{label}</span>
    <span className="break-words">{value}</span>
  </div>
);

const TextBlock: React.FC<{ label: string; value: string }> = ({
  label,
  value,
}) => (
  <div className="space-y-1">
    <h2 className="text-sm font-semibold">{label}</h2>
    <pre className="max-h-96 overflow-auto rounded-md border bg-muted p-3 text-xs whitespace-pre-wrap break-words">
      {value || "(empty)"}
    </pre>
  </div>
);

const LLMCallDetailContent: React.FC<{ call: LLMCallDetailType }> = ({
  call,
}) => (
  <div className="space-y-6">
    <div className="space-y-1">
      <MetaRow
        label="Stage"
        value={<Badge variant="outline">{call.stage}</Badge>}
      />
      <MetaRow
        label="Status"
        value={
          call.status === "error" ? (
            <Badge variant="destructive">error</Badge>
          ) : (
            call.status
          )
        }
      />
      <MetaRow label="Nation" value={call.nation ?? "Unknown"} />
      <MetaRow label="Model" value={call.model} />
      <MetaRow label="Game" value={call.gameId ?? "—"} />
      <MetaRow label="Phase" value={call.phaseName} />
      <MetaRow
        label="Started"
        value={new Date(call.createdAt).toLocaleString()}
      />
      <MetaRow
        label="Latency"
        value={call.latencyMs !== null ? `${call.latencyMs} ms` : "—"}
      />
      <MetaRow
        label="Tokens"
        value={`${call.totalTokens} total (${call.inputTokens} in / ${call.outputTokens} out, cache ${call.cacheReadTokens} read / ${call.cacheWriteTokens} write)`}
      />
    </div>

    {call.errorMessage && (
      <TextBlock label="Error" value={call.errorMessage} />
    )}
    <TextBlock label="System" value={call.system} />
    <TextBlock label="Input" value={call.userContent} />
    <TextBlock label="Output" value={call.response} />
  </div>
);

const LLMCallDetail: React.FC = () => {
  const { llmCallId } = useRequiredParams<{ llmCallId: string }>();
  const { data: call } = useLlmCallsRetrieveSuspense(Number(llmCallId));
  return <LLMCallDetailContent call={call} />;
};

const LLMCallDetailScreen: React.FC = () => {
  const navigate = useNavigate();
  return (
    <ScreenContainer>
      <ScreenHeader
        title="LLM Call"
        actions={
          <Button variant="ghost" size="sm" onClick={() => navigate(-1)}>
            <ArrowLeft className="size-4" />
            Back
          </Button>
        }
      />
      <QueryErrorBoundary>
        <Suspense fallback={<div></div>}>
          <LLMCallDetail />
        </Suspense>
      </QueryErrorBoundary>
    </ScreenContainer>
  );
};

export { LLMCallDetailScreen };
