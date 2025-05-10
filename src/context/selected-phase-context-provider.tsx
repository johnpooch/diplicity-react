import React, { useState, useEffect } from "react";
import { useLocation, useNavigate } from "react-router";
import { SelectedPhaseContext, useSelectedGameContext } from "../common";

const SelectedPhaseContextProvider: React.FC<{
  children: React.ReactNode;
}> = ({ children }) => {
  const { gameRetrieveQuery } = useSelectedGameContext();
  const location = useLocation();
  const navigate = useNavigate();

  // const listPhasesQuery = service.endpoints.listPhases.useQuery(gameId);

  const [selectedPhase, setSelectedPhase] = useState<number | undefined>(() => {
    const params = new URLSearchParams(location.search);
    const phase = params.get("selectedPhase");
    return phase ? Number(phase) : undefined;
  });

  useEffect(() => {
    const params = new URLSearchParams(location.search);
    if (selectedPhase === undefined) {
      params.delete("selectedPhase");
    } else {
      params.set("selectedPhase", selectedPhase.toString());
    }
    navigate({ search: params.toString() }, { replace: true });
  }, [selectedPhase, location.search, navigate]);

  const defaultPhase = gameRetrieveQuery.data
    ? gameRetrieveQuery.data.phases.reduce(
        (max, obj) => (obj.id > max.id ? obj : max),
        gameRetrieveQuery.data.phases[0]
      ).id
    : 1;

  const selectedPhaseOrDefault = selectedPhase || defaultPhase;

  return (
    <SelectedPhaseContext.Provider
      value={{ selectedPhase: selectedPhaseOrDefault, setSelectedPhase }}
    >
      {children}
    </SelectedPhaseContext.Provider>
  );
};

export { SelectedPhaseContextProvider };
