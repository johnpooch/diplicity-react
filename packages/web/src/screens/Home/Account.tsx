import React, { Suspense } from "react";

import { QueryErrorBoundary } from "@/components/QueryErrorBoundary";
import { PlayerProfileContent } from "@/components/PlayerProfileContent";
import { ScreenHeader } from "@/components/ui/screen-header";
import { ScreenContainer } from "@/components/ui/screen-container";

const AccountSuspense: React.FC = () => (
  <ScreenContainer>
    <ScreenHeader title="Account" />
    <QueryErrorBoundary>
      <Suspense fallback={<div></div>}>
        <PlayerProfileContent showAccountSettings />
      </Suspense>
    </QueryErrorBoundary>
  </ScreenContainer>
);

export { AccountSuspense as Account };
