import React from "react";
import { List } from "@mui/material";
import { QueryContainer } from "../../components";
import { ScreenTopBar } from "./screen-top-bar";
import { service } from "../../common";
import { GameCard } from "../../components";

const options = { my: false, mastered: false };

const useFindGames = () => {
  const { endpoints } = service;
  const query = endpoints.listGames.useQuery({
    ...options,
    status: "Open",
  });
  return { query };
};

const FindGames: React.FC = () => {
  const { query } = useFindGames();

  return (
    <>
      <ScreenTopBar title="Find Games" />
      <List sx={{ width: "100%" }} disablePadding>
        <QueryContainer query={query}>
          {(games) =>
            games.map((game) => <GameCard key={game.ID} game={game} />)
          }
        </QueryContainer>
      </List>
    </>
  );
};

export { FindGames };
