import React from "react";
import { List, Fab, useTheme, useMediaQuery } from "@mui/material";
import { Add as AddIcon } from "@mui/icons-material";
import { QueryContainer } from "../../components";
import { service } from "../../common";
import { GameCard } from "../../components";
import { useNavigate } from "react-router";

const styles = {
  fab: {
    position: 'fixed',
    bottom: 72,
    right: 16,
    zIndex: 1000,
  },
} as const;

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
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down("sm"));
  const navigate = useNavigate();

  return (
    <>
      <List sx={{ width: "100%" }} disablePadding>
        <QueryContainer query={query}>
          {(games) => games.map((game) => <GameCard key={game.ID} game={game} />)}
        </QueryContainer>
      </List>
      {isMobile && (
        <Fab 
          color="primary" 
          sx={styles.fab}
          onClick={() => navigate("/create-game")}
          aria-label="create game"
        >
          <AddIcon />
        </Fab>
      )}
    </>
  );
};

export { FindGames };
