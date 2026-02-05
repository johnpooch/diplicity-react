import { Pause } from "lucide-react";
import { formatDateTime, formatRemainingTime } from "@/util";
import { Tooltip, TooltipContent, TooltipTrigger } from "./ui/tooltip";

interface RemainingTimeDisplayProps {
  remainingTime: number;
  scheduledResolution: string;
  isPaused?: boolean;
  className?: string;
}

export const RemainingTimeDisplay: React.FC<RemainingTimeDisplayProps> = ({
  remainingTime,
  scheduledResolution,
  isPaused,
  className,
}) => {
  if (isPaused) {
    return (
      <Tooltip>
        <TooltipTrigger asChild>
          <span className={className} tabIndex={0}>
            <span className="inline-flex items-center gap-1 text-amber-600">
              <Pause className="h-3 w-3" />
              Paused
            </span>
          </span>
        </TooltipTrigger>
        <TooltipContent>
          <p>Game is paused. Deadline will resume when unpaused.</p>
        </TooltipContent>
      </Tooltip>
    );
  }

  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <span className={className} tabIndex={0}>
          {formatRemainingTime(remainingTime)}
        </span>
      </TooltipTrigger>
      <TooltipContent>
        <p>{formatDateTime(scheduledResolution)}</p>
      </TooltipContent>
    </Tooltip>
  );
};
