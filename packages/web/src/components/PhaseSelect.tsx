import { ChevronLeft, ChevronRight } from "lucide-react";
import { useNavigate, useLocation } from "react-router";
import { Button } from "@/components/ui/button";
import { useRequiredParams } from "@/hooks";
import {
  useGamePhaseRetrieveSuspense,
  useGameRetrieveSuspense,
} from "@/api/generated/endpoints";
import { RemainingTimeDisplay } from "./RemainingTimeDisplay";

export const PhaseSelect: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { gameId, phaseId } = useRequiredParams<{
    gameId: string;
    phaseId: string;
  }>();
  const { data: game } = useGameRetrieveSuspense(gameId);
  const { data: phase } = useGamePhaseRetrieveSuspense(gameId, Number(phaseId));

  const goToPreviousPhase = () => {
    if (phase.previousPhaseId) {
      const phasePrefix = `/game/${gameId}/phase/${phaseId}`;
      const suffix = location.pathname.slice(phasePrefix.length);
      navigate(`/game/${gameId}/phase/${phase.previousPhaseId}${suffix}`);
    }
  };

  const goToNextPhase = () => {
    if (phase.nextPhaseId) {
      const phasePrefix = `/game/${gameId}/phase/${phaseId}`;
      const suffix = location.pathname.slice(phasePrefix.length);
      navigate(`/game/${gameId}/phase/${phase.nextPhaseId}${suffix}`);
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
      <div className="flex flex-col items-center min-w-32">
        <span className="text-sm font-medium">{phase.name}</span>
        {phase.status === "active" && phase.scheduledResolution && (
          <RemainingTimeDisplay
            remainingTime={phase.remainingTime}
            scheduledResolution={phase.scheduledResolution}
            isPaused={game.isPaused}
            className="text-xs text-muted-foreground"
          />
        )}
      </div>
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
