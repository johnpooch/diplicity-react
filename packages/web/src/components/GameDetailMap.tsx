import React from "react";
import { Stack } from "@mui/material";
import { service } from "../store";
import { GameDetailLayout } from "../screens/GameDetail/Layout";
import { useParams } from "react-router";
import { GameMap } from "./GameMap";

const GameDetailMap: React.FC = () => {
  const { gameId } = useParams<{ gameId: string }>();
  if (!gameId) throw new Error("gameId is required");

  const query = service.endpoints.gameRetrieve.useQuery({ gameId });

  if (query.isError) {
    return <div>Error</div>;
  }

  return (
    <GameDetailLayout
      // appBar={<HomeAppBar title={query.data?.name || ""} />}
      content={<Stack>
        <GameMap />
      </Stack>}
    />
  );
};

export { GameDetailMap };
