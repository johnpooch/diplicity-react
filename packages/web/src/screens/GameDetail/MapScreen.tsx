import React from "react";
import { service } from "../../store";
import { GameDetailLayout } from "./Layout";
import { useNavigate, useParams } from "react-router";
import { GameMap } from "../../components/GameMap";
import { GameDetailAppBar } from "./AppBar";
import { PhaseSelect } from "../../components/PhaseSelect";

const MapScreen: React.FC = () => {
  const { gameId } = useParams<{ gameId: string }>();
  if (!gameId) throw new Error("gameId is required");

  const query = service.endpoints.gameRetrieve.useQuery({ gameId });
  const navigate = useNavigate();

  if (query.isError) {
    return <div>Error</div>;
  }

  return (
    <GameDetailLayout
      appBar={<GameDetailAppBar title={<PhaseSelect />} onNavigateBack={() => navigate("/")} />}
      content={
        <GameMap />
      }
    />
  );
};

export { MapScreen };
