import React, { Suspense } from "react";

import { QueryErrorBoundary } from "@/components/QueryErrorBoundary";
import { PlayerProfileContent } from "@/components/PlayerProfileContent";
import { ScreenHeader } from "@/components/ui/screen-header";
import { ScreenContainer } from "@/components/ui/screen-container";
import { useRequiredParams } from "@/hooks";

const PlayerProfile: React.FC = () => {
  const { userId } = useRequiredParams<{ userId: string }>();

  return <PlayerProfileContent userId={Number(userId)} />;
};

const PlayerProfileSuspense: React.FC = () => (
  <ScreenContainer>
    <ScreenHeader title="Player Profile" />
    <QueryErrorBoundary>
      <Suspense fallback={<div></div>}>
        <PlayerProfile />
      </Suspense>
    </QueryErrorBoundary>
  </ScreenContainer>
);

export { PlayerProfileSuspense as PlayerProfileScreen };
