import React, { Suspense } from "react";
import { useNavigate } from "react-router";
import { QueryErrorBoundary } from "@/components/QueryErrorBoundary";
import { GameDetailAppBar } from "./AppBar";
import { Panel } from "@/components/Panel";
import { PhaseStepperTitle, PhaseStepperActions } from "@/components/PhaseStepper";
import { GameMap } from "@/components/GameMap";
import { ConfirmOrdersButton } from "@/components/ConfirmOrdersButton";
import { useRequiredParams } from "@/hooks";
import { countOrders } from "@/utils/orderCount";
import { canEnterOrdersForPhase } from "@/utils/orderEntry";
import {
  useGameOrdersListSuspense,
  useGamePhaseRetrieveSuspense,
  useGamePhaseStatesListSuspense,
  useGameRetrieveSuspense,
} from "@/api/generated/endpoints";

const MapConfirmOrders: React.FC = () => {
  const { gameId, phaseId } = useRequiredParams<{
    gameId: string;
    phaseId: string;
  }>();
  const selectedPhase = Number(phaseId);

  const { data: game } = useGameRetrieveSuspense(gameId);
  const { data: phase } = useGamePhaseRetrieveSuspense(gameId, selectedPhase);
  const { data: phaseStates } = useGamePhaseStatesListSuspense(gameId);
  const { data: orders } = useGameOrdersListSuspense(gameId, selectedPhase);

  const members = Array.isArray(game.members) ? game.members : [];
  const currentMember = members.find(m => m.isCurrentUser);
  const canModifyOrders =
    currentMember !== undefined &&
    !currentMember.civilDisorder &&
    !game.sandbox &&
    canEnterOrdersForPhase(game, phase, selectedPhase);

  const count = countOrders(
    Array.isArray(phaseStates) ? phaseStates : [],
    Array.isArray(orders) ? orders : []
  );

  if (!canModifyOrders || !count) return null;

  return (
    <div className="absolute bottom-5 right-16 z-10">
      <ConfirmOrdersButton
        gameId={gameId}
        confirmed={game.phaseConfirmed}
        count={count}
        className="shadow-lg"
      />
    </div>
  );
};

const MapScreen: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="flex flex-col flex-1 min-h-0">
      <GameDetailAppBar
        title={<PhaseStepperTitle />}
        rightButton={<PhaseStepperActions />}
        onNavigateBack={() => navigate("/")}
      />
      <div className="h-[5px] shrink-0" />
      <div className="flex-1 overflow-y-auto">
        <Panel>
          <Panel.Content className="relative">
            <GameMap />
            <Suspense fallback={null}>
              <MapConfirmOrders />
            </Suspense>
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
