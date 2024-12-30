import service from "../store/service";

const useStartedGameQueries = (gameId: string) => {
  const { endpoints } = service;

  const listVariantsQuery = endpoints.listVariants.useQuery(undefined);
  const getGameQuery = endpoints.getGame.useQuery(gameId);
  const listPhasesQuery = endpoints.listPhases.useQuery(gameId);

  const [createOrderMutationTrigger, createOrderQuery] =
    endpoints.createOrder.useMutation();

  const boundCreateOrderMutationTrigger = (parts: string[]) => {
    if (!newestPhaseMeta) throw new Error("No newest phase meta");
    return createOrderMutationTrigger({
      Parts: parts,
      gameId,
      phaseId: newestPhaseMeta.PhaseOrdinal.toString(),
    });
  };

  const newestPhaseMeta = getGameQuery.data?.NewestPhaseMeta;

  const phaseId =
    getGameQuery.data?.NewestPhaseMeta?.PhaseOrdinal.toString() || "";

  const phaseQueryArgs = { gameId, phaseId };
  const phaseQueryOptions = { skip: !newestPhaseMeta };

  const listPhaseStatesQuery = endpoints.listPhaseStates.useQuery(
    phaseQueryArgs,
    phaseQueryOptions
  );

  const listOptionsQuery = endpoints.listOptions.useQuery(
    phaseQueryArgs,
    phaseQueryOptions
  );

  return {
    listVariantsQuery,
    getGameQuery,
    listPhasesQuery,
    listPhaseStatesQuery,
    listOptionsQuery,
    createOrderMutationTrigger: boundCreateOrderMutationTrigger,
    createOrderQuery,
  };
};

export { useStartedGameQueries };