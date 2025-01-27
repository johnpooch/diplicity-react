import { service } from "../../../common";

const useProfile = () => {
    const rootQuery = service.endpoints.getRoot.useQuery(undefined);
    return rootQuery;
}

export { useProfile };