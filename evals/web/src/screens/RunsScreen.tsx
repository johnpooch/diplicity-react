import { Link } from "react-router-dom";
import { Inbox } from "lucide-react";
import { useRuns } from "@/api";
import { Empty, EmptyDescription, EmptyHeader, EmptyMedia, EmptyTitle } from "@/components/ui/empty";
import { formatRun } from "@/labels";

export const RunsScreen: React.FC = () => {
  const { data: runs } = useRuns();

  if (runs.length === 0) {
    return (
      <Empty>
        <EmptyHeader>
          <EmptyMedia variant="icon">
            <Inbox />
          </EmptyMedia>
          <EmptyTitle>No runs yet</EmptyTitle>
          <EmptyDescription>Produce one with `python manage.py run_evals` in evals/.</EmptyDescription>
        </EmptyHeader>
      </Empty>
    );
  }

  return (
    <div className="h-full overflow-y-auto">
      <div className="mx-auto flex max-w-2xl flex-col gap-4 px-6 py-10">
        <h1 className="text-lg font-semibold">Runs</h1>
        <ul className="flex flex-col divide-y">
          {runs.map(run => (
            <li key={run.name}>
              <Link
                to={`/runs/${run.name}`}
                className="flex items-baseline justify-between gap-4 py-3 text-sm hover:underline"
              >
                <span className="font-medium">{formatRun(run.created)}</span>
                <span className="text-muted-foreground">{run.model}</span>
              </Link>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
};
