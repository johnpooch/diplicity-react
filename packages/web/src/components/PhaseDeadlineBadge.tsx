import { Clock } from "lucide-react";
import type { PhaseRetrieve } from "@/api/generated/endpoints";
import { RemainingTimeDisplay } from "./RemainingTimeDisplay";

interface PhaseDeadlineBadgeProps {
  phase: PhaseRetrieve;
  isPaused: boolean;
}

const PhaseDeadlineBadge: React.FC<PhaseDeadlineBadgeProps> = ({
  phase,
  isPaused,
}) => {
  if (phase.status !== "active" || !phase.scheduledResolution) return null;

  return (
    <div className="absolute top-4 left-4 z-10 flex items-center gap-1.5 rounded-full border bg-background/90 px-2 py-1 text-xs font-medium shadow-sm backdrop-blur-sm">
      {!isPaused && <Clock className="size-3.5 text-muted-foreground" />}
      <RemainingTimeDisplay
        remainingTime={phase.remainingTime}
        scheduledResolution={phase.scheduledResolution}
        isPaused={isPaused}
        showResolutionLabel
      />
    </div>
  );
};

export { PhaseDeadlineBadge };
