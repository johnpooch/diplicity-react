import React, { Suspense } from "react";

import { QueryErrorBoundary } from "@/components/QueryErrorBoundary";
import { ScreenHeader } from "@/components/ui/screen-header";
import { ScreenContainer } from "@/components/ui/screen-container";
import { NationAssignmentContent } from "@/components/NationAssignmentContent";

const NationAssignment: React.FC = () => {
  return (
    <ScreenContainer>
      <ScreenHeader title="Nation Assignment" />
      <NationAssignmentContent />
    </ScreenContainer>
  );
};

const NationAssignmentSuspense: React.FC = () => {
  return (
    <div className="w-full">
      <QueryErrorBoundary>
        <Suspense fallback={<div></div>}>
          <NationAssignment />
        </Suspense>
      </QueryErrorBoundary>
    </div>
  );
};

export { NationAssignmentSuspense as NationAssignmentScreen };
