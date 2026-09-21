import { Clock } from "lucide-react";
import type { PhaseRetrieve } from "@/api/generated/endpoints";
import { cn } from "@/lib/utils";
import { RemainingTimeDisplay } from "./RemainingTimeDisplay";

interface PhaseDeadlineBadgeProps {
  phase: PhaseRetrieve;
  isPaused: boolean;
  className?: string;
}

const PhaseDeadlineBadge: React.FC<PhaseDeadlineBadgeProps> = ({
  phase,
  isPaused,
  className,
}) => {
  if (phase.status !== "active" || !phase.scheduledResolution) return null;

  return (
    <div
      className={cn(
        "flex items-center gap-1.5 rounded-full border bg-background/90 px-2 py-1 text-xs font-medium shadow-sm backdrop-blur-sm",
        className
      )}
    >
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
