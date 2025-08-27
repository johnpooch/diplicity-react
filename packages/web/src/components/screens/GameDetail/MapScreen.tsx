import React from "react";
import { service } from "../../../store";
import { GameDetailLayout } from "../../layouts/GameDetailLayout";
import { useNavigate, useParams } from "react-router";
import { Map } from "../../map";
import { GameDetailAppBar } from "../../composites/GameDetailAppBar";
import { PhaseSelect } from "../../composites/PhaseSelect";

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
        <Map />
      }
    />
  );
};

export { MapScreen };
