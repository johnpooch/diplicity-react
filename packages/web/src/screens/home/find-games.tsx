import React from "react";
import { List, Typography } from "@mui/material";
import { QueryContainer } from "../../components";
import { service } from "../../store";
import { GameCard } from "../../components";

const FindGames: React.FC = () => {
  const query = service.endpoints.gamesList.useQuery({ canJoin: true });

  return (
    <List sx={{ width: "100%" }} disablePadding>
      <QueryContainer query={query}>
        {(games) =>
          games.length > 0 ? (
            games.map((game) => <GameCard key={game.id} {...game} />)
          ) : (
            <Typography sx={{ textAlign: "center", marginTop: 2 }}>
              No games available to join.
            </Typography>
          )
        }
      </QueryContainer>
    </List>
  );
};

export { FindGames };
