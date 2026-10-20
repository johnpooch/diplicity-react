import { ChevronLeft, ChevronRight } from "lucide-react";
import type { Feedback, GamePhase } from "@/api";
import { Button } from "@/components/ui/button";
import { failed, phaseLabel } from "@/games";
import { cn } from "@/lib/utils";

interface PhaseStepperProps {
  phases: GamePhase[];
  current: GamePhase;
  notes: Feedback;
  onSelect: (key: string) => void;
}

const abbreviation = (phase: GamePhase): string => `${phase.phase.season[0]}${phase.phase.type[0]}`;

export const PhaseStepper: React.FC<PhaseStepperProps> = ({ phases, current, notes, onSelect }) => {
  const index = phases.indexOf(current);
  const years = [...new Set(phases.map(phase => phase.phase.year))];

  return (
    <div className="flex items-center gap-3">
      <Button
        variant="outline"
        size="icon-sm"
        aria-label="Previous phase"
        disabled={index === 0}
        onClick={() => onSelect(phases[index - 1].key)}
      >
        <ChevronLeft />
      </Button>
      <ol className="flex min-w-0 flex-1 flex-wrap gap-x-4 gap-y-2">
        {years.map(year => (
          <li key={year} className="flex items-center gap-1">
            <span className="mr-1 text-xs text-muted-foreground tabular-nums">{year}</span>
            {phases
              .filter(phase => phase.phase.year === year)
              .map(phase => {
                const noted = Boolean(notes.phases[phase.key]?.trim());
                const broken = failed(phase);
                const selected = phase === current;
                return (
                  <button
                    key={phase.key}
                    type="button"
                    title={`${phaseLabel(phase.phase)}${broken ? " · failed answer" : ""}${noted ? " · has a note" : ""}`}
                    aria-label={phaseLabel(phase.phase)}
                    aria-current={selected ? "step" : undefined}
                    onClick={() => onSelect(phase.key)}
                    className={cn(
                      "relative h-7 w-8 rounded-md border text-xs font-medium text-muted-foreground hover:bg-accent hover:text-foreground",
                      broken && "border-amber-500 bg-amber-50 text-amber-900",
                      selected && "border-foreground bg-foreground text-background hover:bg-foreground hover:text-background"
                    )}
                  >
                    {abbreviation(phase)}
                    {noted && (
                      <span className="absolute -top-1 -right-1 size-2 rounded-full border border-background bg-sky-600" />
                    )}
                  </button>
                );
              })}
          </li>
        ))}
      </ol>
      <Button
        variant="outline"
        size="icon-sm"
        aria-label="Next phase"
        disabled={index === phases.length - 1}
        onClick={() => onSelect(phases[index + 1].key)}
      >
        <ChevronRight />
      </Button>
    </div>
  );
};
