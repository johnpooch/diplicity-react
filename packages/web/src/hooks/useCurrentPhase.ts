import { service } from "../store";

type UseCurrentPhaseParams =
  | {
      id: string;
      phases: number[];
    }
  | undefined;

const getCurrentPhaseId = (phaseIds: number[]): number | undefined => {
  if (!phaseIds || phaseIds.length === 0) return undefined;
  return phaseIds[phaseIds.length - 1];
};

export const useCurrentPhase = (game: UseCurrentPhaseParams) => {
  const currentPhaseId = getCurrentPhaseId(game?.phases ?? []);

  const currentPhaseQuery = service.endpoints.gamePhaseRetrieve.useQuery(
    {
      gameId: game?.id ?? "",
      phaseId: currentPhaseId || 0,
    },
    {
      skip: !currentPhaseId || !game?.id,
    }
  );

  return currentPhaseQuery;
};
