import { Suspense } from "react";
import { Link, useParams } from "react-router-dom";
import { useRun, useRuns } from "@/api";
import { RunPrompts } from "@/components/RunPrompts";
import { RunStats } from "@/components/RunStats";
import { ScoreBreakdown } from "@/components/ScoreBreakdown";
import { Button } from "@/components/ui/button";
import { formatRun, formatScore } from "@/labels";

interface RunProps {
  name: string;
}

const Run: React.FC<RunProps> = ({ name }) => {
  const { data: run } = useRun(name);
  const { data: runs } = useRuns();
  const others = runs.filter(other => other.name !== name);
  const previous = runs[runs.findIndex(other => other.name === name) + 1];

  return (
    <div className="h-full overflow-y-auto">
      <div className="mx-auto flex max-w-3xl flex-col gap-12 px-6 py-10">
        <header className="flex flex-col gap-6">
          <div>
            <Link to="/runs" className="text-sm text-muted-foreground hover:underline">
              Runs
            </Link>
            <h1 className="text-lg font-semibold">{formatRun(run.created)}</h1>
            <p className="text-sm text-muted-foreground">
              {run.model} · <span className="font-mono">{run.id}</span>
            </p>
          </div>
          <div className="flex items-end justify-between gap-6">
            <p className="text-5xl font-semibold tabular-nums">
              {formatScore(run.score)}
              <span className="ml-2 text-xl font-normal text-muted-foreground">reasonable</span>
            </p>
            {run.new > 0 && (
              <Button asChild size="lg">
                <Link to={`/runs/${name}/review`}>Review {run.new} unmarked</Link>
              </Button>
            )}
          </div>
          <ScoreBreakdown counts={run} />
          <RunStats counts={run} epochs={run.epochs} />
        </header>
        <section className="flex flex-col gap-2">
          <h2 className="font-semibold">Fixtures</h2>
          <ul className="flex flex-col divide-y">
            {run.fixtures.map(fixture => (
              <li key={fixture.id}>
                <Link
                  to={`/runs/${name}/fixtures/${fixture.id}`}
                  className="flex items-center gap-4 py-2 text-sm hover:bg-accent"
                >
                  <span className="min-w-0 flex-1 truncate">{fixture.id}</span>
                  {fixture.new > 0 && <span className="text-muted-foreground">{fixture.new} unmarked</span>}
                  {fixture.failed > 0 && <span className="text-muted-foreground">{fixture.failed} failed</span>}
                  <span className="w-24">
                    <ScoreBreakdown counts={fixture} compact />
                  </span>
                  <span className="w-28 text-right tabular-nums">
                    <span className="font-medium">{formatScore(fixture.score)}</span>
                    <span className="text-muted-foreground"> reasonable</span>
                  </span>
                </Link>
              </li>
            ))}
          </ul>
        </section>
        <Suspense fallback={<p className="text-sm text-muted-foreground">Loading…</p>}>
          <RunPrompts run={name} others={others} previous={previous} />
        </Suspense>
      </div>
    </div>
  );
};

export const RunScreen: React.FC = () => {
  const { runName } = useParams();
  return runName ? <Run key={runName} name={runName} /> : null;
};
