import React, { Suspense } from "react";
import { GameDetailAppBar } from "./AppBar";
import { Panel } from "@/components/Panel";
import { QueryErrorBoundary } from "@/components/QueryErrorBoundary";
import { NationPreferenceContent } from "@/components/NationPreferenceContent";
import { Skeleton } from "@/components/ui/skeleton";
import { useGameRetrieveSuspense } from "@/api/generated/endpoints";
import { useRequiredParams } from "@/hooks";

const NationPreferenceContentInGame: React.FC = () => {
  const { gameId, phaseId } = useRequiredParams<{
    gameId: string;
    phaseId: string;
  }>();
  const { data: game } = useGameRetrieveSuspense(gameId);
  const currentMember = game.members.find(member => member.isCurrentUser);
  const base = `/game/${gameId}/phase/${phaseId}`;

  return (
    <NationPreferenceContent
      savedPath={
        currentMember
          ? `${base}/member/${currentMember.id}`
          : `${base}/player-info`
      }
    />
  );
};

const NationPreferenceSkeleton: React.FC = () => (
  <>
    <Skeleton className="h-5 w-64" />
    <Skeleton className="h-80 w-full rounded-xl" />
    <Skeleton className="h-9 w-full" />
  </>
);

const NationPreferenceScreen: React.FC = () => (
  <div className="flex flex-col flex-1 min-h-0">
    <GameDetailAppBar title="Nation Preferences" variant="secondary" />
    <div className="flex-1 overflow-y-auto">
      <Panel>
        <Panel.Content className="flex flex-col gap-4 px-3 py-4 md:p-2">
          <QueryErrorBoundary>
            <Suspense fallback={<NationPreferenceSkeleton />}>
              <NationPreferenceContentInGame />
            </Suspense>
          </QueryErrorBoundary>
        </Panel.Content>
      </Panel>
    </div>
  </div>
);

export { NationPreferenceScreen };
