import { useSelectedGameContext, useSelectedPhaseContext } from "../context";
import { InteractiveMap } from "./interactive-map/interactive-map";
import { QueryContainer } from "./query-container";

const Map: React.FC = () => {
  const { selectedPhase } = useSelectedPhaseContext();
  const { gameRetrieveQuery } = useSelectedGameContext();

  return (
    <QueryContainer query={gameRetrieveQuery}>
      {(game) => {
        const phase = game.phases.find((p) => p.id === selectedPhase);
        if (!phase) throw new Error("Phase not found");
        return (
          <div
            style={{
              height: "100%",
              width: "100%",
            }}
          >
            <InteractiveMap
              interactive
              variant={game.variant}
              phase={phase}
              orders={{}}
            />
          </div>
        );
      }}
    </QueryContainer>
  );
};

export { Map };
