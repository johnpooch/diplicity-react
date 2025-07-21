import React from "react";
import { Stack } from "@mui/material";
import { service } from "../../store";
import { HomeAppBar } from "../composites/HomeAppBar";
import { GameDetailLayout } from "../layouts/GameDetailLayout";
import { useParams } from "react-router";

interface GameDetailProps {
  panel: "orders" | "chat";
}

const GameDetail: React.FC<GameDetailProps> = () => {
  const { gameId } = useParams<{ gameId: string }>();
  if (!gameId) throw new Error("gameId is required");

  const query = service.endpoints.gameRetrieve.useQuery({ gameId });

  if (query.isError) {
    return <div>Error</div>;
  }

  return (
    <GameDetailLayout
      appBar={<HomeAppBar title={query.data?.name || ""} />}
      content={<Stack></Stack>}
    />
  );
};

export { GameDetail };
