import { Suspense } from "react";
import { Navigate } from "react-router";
import { useRequiredParams } from "@/hooks";
import { useGameRetrieveSuspense } from "@/api/generated/endpoints";

const GameReplaceRedirectInner: React.FC = () => {
  const { gameId, memberId } = useRequiredParams<{
    gameId: string;
    memberId: string;
  }>();
  const { data: game } = useGameRetrieveSuspense(gameId);

  if (!game.currentPhaseId) return <Navigate to={`/game-info/${gameId}`} replace />;

  return (
    <Navigate
      to={`/game/${gameId}/phase/${game.currentPhaseId}/replace/${memberId}`}
      replace
    />
  );
};

export const GameReplaceRedirect: React.FC = () => (
  <Suspense fallback={null}>
    <GameReplaceRedirectInner />
  </Suspense>
);
