import React, { useReducer, useEffect, createContext, useContext } from "react";
import { useLocation, useNavigate } from "react-router";
import { useSelectedGameContext } from "./SelectedGameContext";

const SelectedPhaseContext = createContext<
  SelectedPhaseContextType | undefined
>(undefined);

const useSelectedPhaseContext = () => {
  const context = useContext(SelectedPhaseContext);
  if (!context) {
    throw new Error(
      "useSelectedPhaseContext must be used within a PhaseProvider"
    );
  }
  return context;
};

type SelectedPhaseContextType = {
  selectedPhase: number;
  setPhase: (phase: number) => void;
  setPreviousPhase: () => void;
  setNextPhase: () => void;
};

type State = {
  selectedPhase: number | undefined;
};

type Action =
  | { type: "SET_PHASE"; payload: number }
  | {
      type: "SET_PREVIOUS_PHASE";
      payload: { phases: Array<{ id: number; ordinal: number }> };
    }
  | {
      type: "SET_NEXT_PHASE";
      payload: { phases: Array<{ id: number; ordinal: number }> };
    };

const reducer = (state: State, action: Action): State => {
  switch (action.type) {
    case "SET_PHASE":
      return { selectedPhase: action.payload };
    case "SET_PREVIOUS_PHASE": {
      if (state.selectedPhase === undefined) return state;
      const currentIndex = action.payload.phases.findIndex(
        p => p.id === state.selectedPhase
      );
      if (currentIndex > 0) {
        return { selectedPhase: action.payload.phases[currentIndex - 1].id };
      }
      return state;
    }
    case "SET_NEXT_PHASE": {
      if (state.selectedPhase === undefined) return state;
      const currentIndex = action.payload.phases.findIndex(
        p => p.id === state.selectedPhase
      );
      if (currentIndex < action.payload.phases.length - 1) {
        return { selectedPhase: action.payload.phases[currentIndex + 1].id };
      }
      return state;
    }
    default:
      return state;
  }
};

const SelectedPhaseContextProvider: React.FC<{
  children: React.ReactNode;
}> = ({ children }) => {
  const location = useLocation();
  const navigate = useNavigate();

  const [state, dispatch] = useReducer(reducer, undefined, () => {
    const params = new URLSearchParams(location.search);
    const phase = params.get("selectedPhase");
    return { selectedPhase: phase ? Number(phase) : undefined };
  });

  const { gameRetrieveQuery } = useSelectedGameContext();

  useEffect(() => {
    if (!phases) return;
    const defaultPhase = phases[phases.length - 1].id;
    dispatch({ type: "SET_PHASE", payload: defaultPhase });
  }, [gameRetrieveQuery.data?.phases]);

  useEffect(() => {
    const params = new URLSearchParams(location.search);
    if (state.selectedPhase === undefined) {
      params.delete("selectedPhase");
    } else {
      params.set("selectedPhase", state.selectedPhase.toString());
    }
    navigate({ search: params.toString() }, { replace: true });
  }, [state.selectedPhase, location.search, navigate]);

  const phases = gameRetrieveQuery.data?.phases;

  const setPhase = (phase: number) => {
    dispatch({ type: "SET_PHASE", payload: phase });
  };

  const setPreviousPhase = () => {
    if (!phases) return;
    dispatch({ type: "SET_PREVIOUS_PHASE", payload: { phases } });
  };

  const setNextPhase = () => {
    if (!phases) return;
    dispatch({ type: "SET_NEXT_PHASE", payload: { phases } });
  };

  const selectedPhaseOrDefault =
    state.selectedPhase ?? phases?.[phases.length - 1].id;

  return (
    <SelectedPhaseContext.Provider
      value={{
        selectedPhase: selectedPhaseOrDefault ?? 1,
        setPhase,
        setPreviousPhase,
        setNextPhase,
      }}
    >
      {children}
    </SelectedPhaseContext.Provider>
  );
};

export { SelectedPhaseContextProvider, useSelectedPhaseContext };
