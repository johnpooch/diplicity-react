import { Typography } from "@mui/material";
import { service } from "../../common";
import { useGameDetailContext } from "../../context";
import { QueryContainer } from "../query-container";

const GameName: React.FC = () => {
  const { gameId } = useGameDetailContext();
  const getGameQuery = service.endpoints.getGame.useQuery(gameId);

  return (
    <QueryContainer query={getGameQuery} onRenderLoading={() => <></>}>
      {(data) => <Typography variant="h1"> {data.Desc.charAt(0).toUpperCase() + data.Desc.slice(1)}</Typography>}
    </QueryContainer>
  );
};

export { GameName };
