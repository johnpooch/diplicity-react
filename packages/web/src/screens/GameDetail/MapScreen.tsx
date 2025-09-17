import React from "react";
import { GameDetailLayout } from "./Layout";
import { useNavigate } from "react-router";
import { GameMap } from "../../components/GameMap";
import { GameDetailAppBar } from "./AppBar";
import { PhaseSelect } from "../../components/PhaseSelect";

const MapScreen: React.FC = () => {
  const navigate = useNavigate();

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
