import { formatDateTime, formatRemainingTime } from "@/util";
import { Tooltip, TooltipContent, TooltipTrigger } from "./ui/tooltip";

interface RemainingTimeDisplayProps {
  remainingTime: number;
  scheduledResolution: string;
  className?: string;
}

export const RemainingTimeDisplay: React.FC<RemainingTimeDisplayProps> = ({
  remainingTime,
  scheduledResolution,
  className,
}) => {
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <span className={className}>{formatRemainingTime(remainingTime)}</span>
      </TooltipTrigger>
      <TooltipContent>
        <p>{formatDateTime(scheduledResolution)}</p>
      </TooltipContent>
    </Tooltip>
  );
};
