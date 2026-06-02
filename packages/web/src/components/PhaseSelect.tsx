import { useEffect, useRef } from "react";
import { ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight } from "lucide-react";
import { useNavigate, useLocation } from "react-router";
import { toast } from "sonner";
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

  const isOnLatestPhase = !game.currentPhaseId || game.currentPhaseId === Number(phaseId);
  const isOnFirstPhase = phase.previousPhaseId === null;

  const getPathSuffix = () => {
    const phasePrefix = `/game/${gameId}/phase/${phaseId}`;
    return location.pathname.slice(phasePrefix.length);
  };

  const goToFirstPhase = () => {
    const firstPhaseId = game.phases[0];
    if (!firstPhaseId) return;
    navigate(`/game/${gameId}/phase/${firstPhaseId}${getPathSuffix()}`);
  };

  const goToPreviousPhase = () => {
    if (phase.previousPhaseId) {
      navigate(`/game/${gameId}/phase/${phase.previousPhaseId}${getPathSuffix()}`);
    }
  };

  const goToNextPhase = () => {
    if (phase.nextPhaseId) {
      navigate(`/game/${gameId}/phase/${phase.nextPhaseId}${getPathSuffix()}`);
    }
  };

  const goToLatestPhase = () => {
    if (!game.currentPhaseId) return;
    navigate(`/game/${gameId}/phase/${game.currentPhaseId}${getPathSuffix()}`);
  };

  const prevCurrentPhaseIdRef = useRef(game.currentPhaseId);

  useEffect(() => {
    const prevId = prevCurrentPhaseIdRef.current;
    if (game.currentPhaseId !== prevId && prevId !== null) {
      const newPhaseId = game.currentPhaseId;
      if (newPhaseId) {
        const phasePrefix = `/game/${gameId}/phase/${phaseId}`;
        const suffix = location.pathname.slice(phasePrefix.length);
        toast.success("A new phase has started", {
          duration: 10000,
          action: {
            label: "Jump to newest",
            onClick: () => navigate(`/game/${gameId}/phase/${newPhaseId}${suffix}`),
          },
        });
      }
    }
    prevCurrentPhaseIdRef.current = game.currentPhaseId;
    // eslint-disable-next-line react-hooks/exhaustive-deps -- only fire on currentPhaseId change
  }, [game.currentPhaseId]);

  return (
    <div className="flex items-center gap-1">
      <Button
        variant="ghost"
        size="icon"
        className="h-7 w-7"
        onClick={goToFirstPhase}
        disabled={isOnFirstPhase}
        aria-label="First phase"
      >
        <ChevronsLeft className="h-3.5 w-3.5" />
      </Button>
      <Button
        variant="ghost"
        size="icon"
        className="h-7 w-7"
        onClick={goToPreviousPhase}
        disabled={phase.previousPhaseId === null}
        aria-label="Previous phase"
      >
        <ChevronLeft className="h-3.5 w-3.5" />
      </Button>
      <div className="flex flex-col items-center">
        <span className="text-xs font-medium">{phase.name}</span>
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
        className="h-7 w-7"
        onClick={goToNextPhase}
        disabled={phase.nextPhaseId === null}
        aria-label="Next phase"
      >
        <ChevronRight className="h-3.5 w-3.5" />
      </Button>
      <Button
        variant="ghost"
        size="icon"
        className="h-7 w-7"
        onClick={goToLatestPhase}
        disabled={isOnLatestPhase}
        aria-label="Latest phase"
      >
        <ChevronsRight className="h-3.5 w-3.5" />
      </Button>
    </div>
  );
};
