import React, { Suspense } from "react";

import { QueryErrorBoundary } from "@/components/QueryErrorBoundary";
import { ScreenHeader } from "@/components/ui/screen-header";
import { ScreenContainer } from "@/components/ui/screen-container";
import { NationPreferenceContent } from "@/components/NationPreferenceContent";

const NationPreference: React.FC = () => {
  return (
    <ScreenContainer>
      <ScreenHeader title="Nation Preferences" />
      <NationPreferenceContent />
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
