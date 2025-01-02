import { useLocation, useNavigate } from "react-router";
import { useJoinGameMutation, useLeaveGameMutation } from "../../common";

const useGameCard = (id: string) => {
    const location = useLocation();
    const navigate = useNavigate();

    const [joinGame] = useJoinGameMutation(id);
    const [leaveGame] = useLeaveGameMutation(id);

    const onClickGameInfo = () => {
        const query = new URLSearchParams(location.search);
        query.set("gameInfo", id);
        navigate({ search: query.toString() });
    }
    const onClickPlayerInfo = () => {
        const query = new URLSearchParams(location.search);
        query.set("playerInfo", id);
        navigate({ search: query.toString() });
    }
    const onClickShare = () => {
        navigator.clipboard.writeText(`${window.location.origin}/game/${id}`);
    }
    const onClickJoin = () => {
        joinGame();
    }
    const onClickLeave = () => {
        leaveGame();
    }
    const onClickViewGame = () => {
        navigate(`/game/${id}`);
    }
    return {
        onClickGameInfo,
        onClickPlayerInfo,
        onClickShare,
        onClickJoin,
        onClickLeave,
        onClickViewGame,
    };
}

export { useGameCard };