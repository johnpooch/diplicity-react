import React, { Suspense } from "react";
import { useRequiredParams } from "@/hooks";

import { QueryErrorBoundary } from "@/components/QueryErrorBoundary";
import { ScreenHeader } from "@/components/ui/screen-header";
import { ScreenContainer } from "@/components/ui/screen-container";
import { NationPreferenceContent } from "@/components/NationPreferenceContent";

const NationPreference: React.FC = () => {
  const { gameId } = useRequiredParams<{ gameId: string }>();
  return (
    <ScreenContainer>
      <ScreenHeader title="Nation Preferences" />
      <NationPreferenceContent savedPath={`/game-info/${gameId}`} />
    </ScreenContainer>
  );
};

const NationPreferenceSuspense: React.FC = () => {
  return (
    <div className="w-full">
      <QueryErrorBoundary>
        <Suspense fallback={<div></div>}>
          <NationPreference />
        </Suspense>
      </QueryErrorBoundary>
    </div>
  );
};

export { NationPreferenceSuspense as NationPreferenceScreen };
