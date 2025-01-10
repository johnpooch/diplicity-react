import { useLocation, useNavigate } from "react-router";
import { mergeQueries, useGetCurrentPhaseQuery } from "../../common";
import { useGameDetailContext } from "../../context";

const useCreateOrderAction = () => {
    const { gameId } = useGameDetailContext();
    const location = useLocation();
    const navigate = useNavigate();

    const currentPhaseQuery = useGetCurrentPhaseQuery(gameId);

    const handleClick = () => {
        const searchParams = new URLSearchParams(location.search);
        searchParams.set("createOrder", "true");
        navigate({ search: searchParams.toString() });
    };

    const mergedQuery = mergeQueries([currentPhaseQuery], (phase) => ({
        canCreateOrder: Boolean(phase.canCreateOrder),
    }));

    return {
        ...mergedQuery,
        handleClick,
    };
};

export { useCreateOrderAction };