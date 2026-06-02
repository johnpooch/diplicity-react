import { Suspense } from "react";
import { Navigate, useLocation } from "react-router";
import { useRequiredParams } from "@/hooks";
import { useIsMobile } from "@/hooks/use-mobile";
import { useGameRetrieveSuspense } from "@/api/generated/endpoints";
import { getGameLandingPath } from "@/util";
import { QueryErrorBoundary } from "@/components/QueryErrorBoundary";
import { useAuth } from "@/auth";
import { deepLinkStorage } from "@/deepLink";

const GamePhaseRedirectInner: React.FC = () => {
  const { gameId } = useRequiredParams<{ gameId: string }>();
  const { data: game } = useGameRetrieveSuspense(gameId);
  const isMobile = useIsMobile();
  const { loggedIn } = useAuth();
  const location = useLocation();

  if (game.private && !loggedIn) {
    deepLinkStorage.setPendingPath(location.pathname);
    return <Navigate to="/" replace />;
  }

  return <Navigate to={getGameLandingPath(game, isMobile)} replace />;
};

export const GamePhaseRedirect: React.FC = () => (
  <QueryErrorBoundary>
    <Suspense fallback={null}>
      <GamePhaseRedirectInner />
    </Suspense>
  </QueryErrorBoundary>
);
