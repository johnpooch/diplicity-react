import { service } from "../store"
import { mergeQueries } from "./common";

const useGetUserConfigQuery = () => {
    const getRootQuery = service.endpoints.getRoot.useQuery(undefined);
    const getUserConfigQuery = service.endpoints.getUserConfig.useQuery(getRootQuery.data?.Id || "", {
        skip: !getRootQuery.data?.Id,
    })
    return mergeQueries([getUserConfigQuery], (data) => {
        return data;
    })
}

export { useGetUserConfigQuery }