import { Suspense } from "react";
import { Navigate } from "react-router";
import { useRequiredParams } from "@/hooks";
import { useIsMobile } from "@/hooks/use-mobile";
import { useGameRetrieveSuspense } from "@/api/generated/endpoints";

const GamePhaseRedirectInner: React.FC = () => {
  const { gameId } = useRequiredParams<{ gameId: string }>();
  const { data: game } = useGameRetrieveSuspense(gameId);
  const isMobile = useIsMobile();

  if (!game.currentPhaseId) {
    return <Navigate to="/" replace />;
  }

  const basePath = `/game/${gameId}/phase/${game.currentPhaseId}`;
  const redirectPath = isMobile ? basePath : `${basePath}/orders`;

  return <Navigate to={redirectPath} replace />;
};

export const GamePhaseRedirect: React.FC = () => (
  <Suspense fallback={null}>
    <GamePhaseRedirectInner />
  </Suspense>
);
