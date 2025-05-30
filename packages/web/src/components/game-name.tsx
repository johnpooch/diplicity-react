import { Typography } from "@mui/material";
import { QueryContainer } from "./query-container";
import { useSelectedGameContext } from "../context";

const GameName: React.FC = () => {
  const { gameRetrieveQuery } = useSelectedGameContext();

  return (
    <QueryContainer query={gameRetrieveQuery} onRenderLoading={() => <></>}>
      {(game) => <Typography variant="h1">{game.name}</Typography>}
    </QueryContainer>
  );
};

export { GameName };
