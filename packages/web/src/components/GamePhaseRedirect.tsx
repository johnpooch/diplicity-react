import { Suspense } from "react";
import { Navigate } from "react-router";
import { useRequiredParams } from "@/hooks";
import { useIsMobile } from "@/hooks/use-mobile";
import { useGameRetrieveSuspense } from "@/api/generated/endpoints";
import { getGameLandingPath } from "@/util";
import { QueryErrorBoundary } from "@/components/QueryErrorBoundary";

const GamePhaseRedirectInner: React.FC = () => {
  const { gameId } = useRequiredParams<{ gameId: string }>();
  const { data: game } = useGameRetrieveSuspense(gameId);
  const isMobile = useIsMobile();

  return <Navigate to={getGameLandingPath(game, isMobile)} replace />;
};

export const GamePhaseRedirect: React.FC = () => (
  <QueryErrorBoundary>
    <Suspense fallback={null}>
      <GamePhaseRedirectInner />
    </Suspense>
  </QueryErrorBoundary>
);
