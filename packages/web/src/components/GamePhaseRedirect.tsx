import { Suspense } from "react";
import { Navigate } from "react-router";
import { useRequiredParams } from "@/hooks";
import { useGameRetrieveSuspense } from "@/api/generated/endpoints";

const GamePhaseRedirectInner: React.FC = () => {
  const { gameId } = useRequiredParams<{ gameId: string }>();
  const { data: game } = useGameRetrieveSuspense(gameId);

  if (!game.currentPhaseId) {
    return <Navigate to="/" replace />;
  }

  return (
    <Navigate to={`/game/${gameId}/phase/${game.currentPhaseId}/orders`} replace />
  );
};

export const GamePhaseRedirect: React.FC = () => (
  <Suspense fallback={null}>
    <GamePhaseRedirectInner />
  </Suspense>
);
