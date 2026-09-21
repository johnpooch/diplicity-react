import { useEffect, useRef, useState } from "react";
import { useNavigate, useLocation } from "react-router";
import { toast } from "sonner";
import { Check, ChevronLeft, ChevronRight, ChevronsUpDown } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { useRequiredParams } from "@/hooks";
import {
  useGamePhasesListSuspense,
  useGamePhaseRetrieveSuspense,
  useGameRetrieveSuspense,
} from "@/api/generated/endpoints";

const usePathSuffix = () => {
  const { gameId, phaseId } = useRequiredParams<{
    gameId: string;
    phaseId: string;
  }>();
  const location = useLocation();
  const phasePrefix = `/game/${gameId}/phase/${phaseId}`;
  return location.pathname.slice(phasePrefix.length);
};

const PhaseStepperTitle: React.FC = () => {
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const { gameId, phaseId } = useRequiredParams<{
    gameId: string;
    phaseId: string;
  }>();
  const suffix = usePathSuffix();

  const { data: game } = useGameRetrieveSuspense(gameId);
  const { data: phase } = useGamePhaseRetrieveSuspense(gameId, Number(phaseId));
  const { data: phases } = useGamePhasesListSuspense(gameId);

  const goTo = (id: number) => {
    navigate(`/game/${gameId}/phase/${id}${suffix}`);
  };

  const prevCurrentPhaseIdRef = useRef(game.currentPhaseId);

  useEffect(() => {
    const prevId = prevCurrentPhaseIdRef.current;
    if (game.currentPhaseId !== prevId && prevId !== null) {
      const newPhaseId = game.currentPhaseId;
      if (newPhaseId) {
        toast.success("A new phase has started", {
          duration: 10000,
          action: {
            label: "Jump to newest",
            onClick: () => goTo(newPhaseId),
          },
        });
      }
    }
    prevCurrentPhaseIdRef.current = game.currentPhaseId;
    // eslint-disable-next-line react-hooks/exhaustive-deps -- only fire on currentPhaseId change
  }, [game.currentPhaseId]);

  const orderedPhases = [...phases].reverse();

  return (
    <div className="min-h-12 min-w-0 flex-1 pt-1.5 md:min-h-14 md:pt-2.5">
      <Popover open={open} onOpenChange={setOpen}>
        <PopoverTrigger asChild>
          <button
            type="button"
            aria-label={`${phase.name}. Choose phase`}
            className="group flex max-w-full items-center gap-1 rounded-md text-left transition-colors hover:bg-accent hover:text-accent-foreground"
          >
            <span className="min-w-0 truncate text-base font-semibold leading-7 md:text-xl md:leading-9">
              {phase.name}
            </span>
            <ChevronsUpDown className="size-4 shrink-0 text-muted-foreground transition-colors group-hover:text-accent-foreground" />
          </button>
        </PopoverTrigger>
        <PopoverContent align="start" className="w-72 p-1">
          <div className="flex max-h-80 flex-col overflow-y-auto">
            {orderedPhases.map(p => (
              <button
                key={p.id}
                type="button"
                className="flex w-full items-center gap-2 rounded-sm px-2 py-1.5 text-left hover:bg-accent hover:text-accent-foreground"
                onClick={() => {
                  goTo(p.id);
                  setOpen(false);
                }}
              >
                <span className="min-w-0 flex-1 truncate text-sm font-medium">
                  {p.name}
                </span>
                {p.status === "active" && (
                  <span className="text-xs font-medium text-muted-foreground">
                    Current
                  </span>
                )}
                {p.id === Number(phaseId) && (
                  <Check className="size-4 shrink-0" aria-hidden />
                )}
              </button>
            ))}
          </div>
        </PopoverContent>
      </Popover>
      {phase.status !== "active" && (
        <span className="block text-xs text-muted-foreground">Resolved</span>
      )}
    </div>
  );
};

const PhaseStepperActions: React.FC = () => {
  const navigate = useNavigate();
  const { gameId, phaseId } = useRequiredParams<{
    gameId: string;
    phaseId: string;
  }>();
  const suffix = usePathSuffix();
  const { data: phase } = useGamePhaseRetrieveSuspense(gameId, Number(phaseId));

  const goToPrevious = () => {
    if (phase.previousPhaseId) {
      navigate(`/game/${gameId}/phase/${phase.previousPhaseId}${suffix}`);
    }
  };

  const goToNext = () => {
    if (phase.nextPhaseId) {
      navigate(`/game/${gameId}/phase/${phase.nextPhaseId}${suffix}`);
    }
  };

  return (
    <div className="flex items-center gap-1">
      <Button
        variant="outline"
        size="icon"
        onClick={goToPrevious}
        disabled={phase.previousPhaseId === null}
        aria-label="Previous phase"
      >
        <ChevronLeft />
      </Button>
      <Button
        variant="outline"
        size="icon"
        onClick={goToNext}
        disabled={phase.nextPhaseId === null}
        aria-label="Next phase"
      >
        <ChevronRight />
      </Button>
    </div>
  );
};

export { PhaseStepperTitle, PhaseStepperActions };
