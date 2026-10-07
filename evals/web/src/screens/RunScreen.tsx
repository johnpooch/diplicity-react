import { Suspense } from "react";
import { Link, useParams } from "react-router-dom";
import { useRun, useRuns } from "@/api";
import { RunPrompts } from "@/components/RunPrompts";
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
            <p className="text-sm text-muted-foreground">{run.model}</p>
          </div>
          <div className="flex items-end justify-between gap-6">
            <div>
              <p className="text-5xl font-semibold tabular-nums">{formatScore(run.score)}</p>
              <p className="mt-1 text-sm text-muted-foreground">
                {run.reasonable} of {run.order_sets} distinct order sets reasonable
                {run.unanswered > 0 && ` · ${run.unanswered} unusable ${run.unanswered === 1 ? "answer" : "answers"}`}
              </p>
            </div>
            {run.new > 0 && (
              <Button asChild size="lg">
                <Link to={`/runs/${name}/review`}>Review {run.new} new</Link>
              </Button>
            )}
          </div>
        </header>
        <section className="flex flex-col gap-2">
          <h2 className="font-semibold">Fixtures</h2>
          <ul className="flex flex-col divide-y">
            {run.fixtures.map(fixture => (
              <li key={fixture.id} className="flex items-baseline gap-4 py-2 text-sm">
                <Link to={`/fixtures/${fixture.id}`} className="min-w-0 flex-1 truncate hover:underline">
                  {fixture.id}
                </Link>
                {fixture.new > 0 && <span className="text-muted-foreground">{fixture.new} new to review</span>}
                <span className="w-12 text-right font-medium tabular-nums">{formatScore(fixture.score)}</span>
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
