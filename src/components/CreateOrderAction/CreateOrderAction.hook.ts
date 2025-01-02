import { useLocation, useNavigate, useParams } from "react-router";
import { mergeQueries, useGetCurrentPhaseQuery } from "../../common";

const useCreateOrderAction = () => {
    const location = useLocation();
    const navigate = useNavigate();
    const { gameId } = useParams<{ gameId: string }>();

    if (!gameId) throw new Error("No gameId provided");

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