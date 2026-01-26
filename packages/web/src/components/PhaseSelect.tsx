import { ChevronLeft, ChevronRight } from "lucide-react";
import { useNavigate, useLocation } from "react-router";
import { Button } from "@/components/ui/button";
import { useRequiredParams } from "@/hooks";
import { useGamePhaseRetrieveSuspense } from "@/api/generated/endpoints";

export const PhaseSelect: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { gameId, phaseId } = useRequiredParams<{
    gameId: string;
    phaseId: string;
  }>();
  const { data: phase } = useGamePhaseRetrieveSuspense(gameId, Number(phaseId));

  const goToPreviousPhase = () => {
    if (phase.previousPhaseId) {
      const newPath = location.pathname.replace(
        `/phase/${phaseId}/`,
        `/phase/${phase.previousPhaseId}/`
      );
      navigate(newPath);
    }
  };

  const goToNextPhase = () => {
    if (phase.nextPhaseId) {
      const newPath = location.pathname.replace(
        `/phase/${phaseId}/`,
        `/phase/${phase.nextPhaseId}/`
      );
      navigate(newPath);
    }
  };

  return (
    <div className="flex items-center gap-1">
      <Button
        variant="ghost"
        size="icon"
        onClick={goToPreviousPhase}
        disabled={phase.previousPhaseId === null}
        aria-label="Previous phase"
      >
        <ChevronLeft className="h-4 w-4" />
      </Button>
      <span className="text-sm font-medium min-w-32 text-center">
        {phase.name}
      </span>
      <Button
        variant="ghost"
        size="icon"
        onClick={goToNextPhase}
        disabled={phase.nextPhaseId === null}
        aria-label="Next phase"
      >
        <ChevronRight className="h-4 w-4" />
      </Button>
    </div>
  );
};
