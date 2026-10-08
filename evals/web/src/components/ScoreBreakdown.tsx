import type { RunCounts } from "@/api";
import { LABELS, UNMARKED, plural } from "@/labels";
import { cn } from "@/lib/utils";

interface ScoreBreakdownProps {
  counts: RunCounts;
  compact?: boolean;
}

export const ScoreBreakdown: React.FC<ScoreBreakdownProps> = ({ counts, compact }) => {
  const parts = [
    ...LABELS.map(option => ({ ...option, count: counts[option.label] })),
    { ...UNMARKED, count: counts.unmarked },
  ];

  return (
    <div className="flex flex-col gap-2">
      <div className={cn("flex overflow-hidden rounded-full bg-muted", compact ? "h-1.5" : "h-2.5")}>
        {parts.map(part => (
          <div key={part.name} className={part.dot} style={{ flexGrow: part.count }} />
        ))}
      </div>
      {!compact && (
        <p className="flex flex-wrap gap-x-4 gap-y-1 text-sm text-muted-foreground">
          {parts.map(part => (
            <span key={part.name} className="flex items-center gap-1.5">
              <span className={`size-2 rounded-full ${part.dot}`} />
              <span className="font-medium text-foreground tabular-nums">{part.count}</span>
              {part.name.toLowerCase()}
            </span>
          ))}
          <span>
            of {plural(counts.answers - counts.failed, "answer")} · {plural(counts.order_sets, "distinct order set")}
          </span>
        </p>
      )}
    </div>
  );
};
