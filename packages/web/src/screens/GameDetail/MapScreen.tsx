import React, { Suspense } from "react";
import { useNavigate } from "react-router";
import { QueryErrorBoundary } from "@/components/QueryErrorBoundary";
import { GameDetailAppBar } from "./AppBar";
import { Panel } from "@/components/Panel";
import { PhaseStepperTitle, PhaseStepperActions } from "@/components/PhaseStepper";
import { GameMap } from "@/components/GameMap";

const MapScreen: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="flex flex-col flex-1 min-h-0">
      <GameDetailAppBar
        title={<PhaseStepperTitle />}
        rightButton={<PhaseStepperActions />}
        onNavigateBack={() => navigate("/")}
      />
      <div className="flex-1 overflow-y-auto">
        <Panel>
          <Panel.Content>
            <GameMap />
          </Panel.Content>
        </Panel>
      </div>
    </div>
  );
};

const MapScreenSuspense: React.FC = () => (
  <QueryErrorBoundary>
    <Suspense fallback={<div></div>}>
      <MapScreen />
    </Suspense>
  </QueryErrorBoundary>
);

export { MapScreenSuspense as MapScreen };
