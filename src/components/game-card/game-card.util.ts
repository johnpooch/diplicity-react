import service from "../../common/store/service";
import { GameCard } from "./game-card";

type Game = typeof service.endpoints.listGames.Types.ResultType[0];

const createGameCardProps = (game: Game): Omit<React.ComponentProps<typeof GameCard>,
    "onClickGameInfo" | "onClickPlayerInfo" | "onClickShare" | "onClickJoin" | "onClickLeave" | "onClickViewGame"
> => {
    return {
        canJoin: game.canJoin,
        canLeave: game.canLeave,
        id: game.ID,
        isPrivate: game.Private,
        members: game.Members.map((member) => ({
            id: member.User.Id,
            src: member.User.Picture,
        })),
        name: game.Desc,
        phase: game.NewestPhaseMeta ? {
            season: game.NewestPhaseMeta.Season,
            year: game.NewestPhaseMeta.Year,
            type: game.NewestPhaseMeta.Type,
            timeRemaining: game.NewestPhaseMeta.NextDeadlineIn,
        } : undefined,
        phaseLength: game.PhaseLengthMinutes,
        status: game.status,
        variant: game.Variant,
    }
};

export { createGameCardProps };