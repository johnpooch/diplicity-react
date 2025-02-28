import { Typography } from "@mui/material";
import { service, useSelectedGameContext } from "../../common";
import { QueryContainer } from "../query-container";

const GameName: React.FC = () => {
  const { gameId } = useSelectedGameContext();
  const getGameQuery = service.endpoints.getGame.useQuery(gameId);

  return (
    <QueryContainer query={getGameQuery} onRenderLoading={() => <></>}>
      {(data) => <Typography variant="h1">{data.Desc}</Typography>}
    </QueryContainer>
  );
};

export { GameName };
