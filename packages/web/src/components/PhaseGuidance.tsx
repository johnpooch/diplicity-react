import { Check } from "lucide-react";
import { useRequiredParams } from "@/hooks";
import {
  useGameRetrieveSuspense,
  useGamePhaseRetrieveSuspense,
  useGameOrdersListSuspense,
  useGamePhaseStatesListSuspense,
} from "@/api/generated/endpoints";

type GuidanceResult = {
  text: string;
  isComplete: boolean;
  isConfirmed: boolean;
} | null;

function usePhaseGuidance(): GuidanceResult {
  const { gameId, phaseId } = useRequiredParams<{
    gameId: string;
    phaseId: string;
  }>();
  const selectedPhase = Number(phaseId);

  const { data: game } = useGameRetrieveSuspense(gameId);
  const { data: phase } = useGamePhaseRetrieveSuspense(gameId, selectedPhase);
  const { data: orders } = useGameOrdersListSuspense(gameId, selectedPhase);
  const { data: phaseStates } = useGamePhaseStatesListSuspense(gameId);

  // Historical phases show no guidance
  if (phase.status !== "active") {
    return null;
  }

  const userMember = game.members.find(m => m.isCurrentUser);
  const userPhaseState = phaseStates.find(ps => ps.member.isCurrentUser);

  // No nation assigned yet (game hasn't started)
  if (!userMember?.nation || !userPhaseState) {
    return null;
  }

  const userNation = userMember.nation;
  const isConfirmed = game.phaseConfirmed;

  switch (phase.type) {
    case "Movement": {
      const totalOrderable = userPhaseState.orderableProvinces.length;
      if (totalOrderable === 0) {
        return { text: "No orders required", isComplete: true, isConfirmed };
      }

      const orderableIds = new Set(
        userPhaseState.orderableProvinces.map(p => p.id)
      );
      const submittedOrders = orders.filter(o => orderableIds.has(o.source.id));
      const submittedCount = submittedOrders.length;

      if (submittedCount === 0) {
        return {
          text: `Submit orders for ${totalOrderable} unit${totalOrderable > 1 ? "s" : ""}`,
          isComplete: false,
          isConfirmed,
        };
      }
      if (submittedCount < totalOrderable) {
        return {
          text: `${submittedCount} of ${totalOrderable} orders submitted`,
          isComplete: false,
          isConfirmed,
        };
      }
      return { text: "All orders submitted", isComplete: true, isConfirmed };
    }

    case "Adjustment": {
      const supplyCenterCount = phase.supplyCenters.filter(
        sc => sc.nation.name === userNation
      ).length;
      const unitCount = phase.units.filter(
        u => u.nation.name === userNation
      ).length;
      const delta = supplyCenterCount - unitCount;

      if (delta === 0) {
        return { text: "No adjustments needed", isComplete: true, isConfirmed };
      }
      if (delta > 0) {
        return {
          text: `Build ${delta} new unit${delta > 1 ? "s" : ""}`,
          isComplete: false,
          isConfirmed,
        };
      }
      return {
        text: `Disband ${Math.abs(delta)} unit${Math.abs(delta) > 1 ? "s" : ""}`,
        isComplete: false,
        isConfirmed,
      };
    }

    case "Retreat": {
      const dislodgedCount = phase.units.filter(
        u => u.dislodged && u.nation.name === userNation
      ).length;

      if (dislodgedCount === 0) {
        return { text: "No retreats required", isComplete: true, isConfirmed };
      }
      return {
        text: `${dislodgedCount} unit${dislodgedCount > 1 ? "s" : ""} must retreat`,
        isComplete: false,
        isConfirmed,
      };
    }

    default:
      return null;
  }
}

export const PhaseGuidance: React.FC = () => {
  const guidance = usePhaseGuidance();

  if (!guidance) {
    return null;
  }

  return (
    <span className="text-xs text-muted-foreground inline-flex items-center gap-1">
      {guidance.text}
      {guidance.isComplete && <Check className="size-3" />}
      <span>·</span>
      <span>{guidance.isConfirmed ? "confirmed" : "not confirmed"}</span>
    </span>
  );
};
