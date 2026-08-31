import React from "react";
import { Navigate, useLocation } from "react-router";
import { useRequiredParams } from "@/hooks";

const PlayerInfoScreen: React.FC = () => {
  const location = useLocation();
  const { gameId, phaseId } = useRequiredParams<{
    gameId: string;
    phaseId: string;
  }>();

  return (
    <Navigate
      replace
      to={{
        pathname: `/game/${gameId}/phase/${phaseId}/overview`,
        search: location.search,
      }}
    />
  );
};

export { PlayerInfoScreen };
