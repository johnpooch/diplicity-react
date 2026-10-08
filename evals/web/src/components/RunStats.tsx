import { Info } from "lucide-react";
import type { RunCounts } from "@/api";

interface RunStatsProps {
  counts: RunCounts;
  epochs: number;
}

const FAILED_HINT = "Answers that were not a legal order set. They do not count towards any other metric.";

const average = (total: number, answers: number): string =>
  answers ? Math.round(total / answers).toLocaleString() : "–";

export const RunStats: React.FC<RunStatsProps> = ({ counts, epochs }) => {
  const stats = [
    { name: "Epochs", value: epochs.toLocaleString() },
    { name: "Failed", value: `${counts.failed}/${counts.answers}`, hint: FAILED_HINT },
    { name: "Avg input tokens", value: average(counts.input_tokens, counts.answers) },
    { name: "Avg output tokens", value: average(counts.output_tokens, counts.answers) },
  ];

  return (
    <dl className="flex flex-wrap gap-x-8 gap-y-3">
      {stats.map(stat => (
        <div key={stat.name}>
          <dt className="flex items-center gap-1 text-xs text-muted-foreground">
            {stat.name}
            {stat.hint && (
              <span title={stat.hint} aria-label={stat.hint} className="cursor-help">
                <Info className="size-3" />
              </span>
            )}
          </dt>
          <dd className="font-medium tabular-nums">{stat.value}</dd>
        </div>
      ))}
    </dl>
  );
};
