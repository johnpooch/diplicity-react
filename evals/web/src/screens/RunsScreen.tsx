import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { ArrowDown, ArrowUp, Inbox } from "lucide-react";
import { useRuns, type RunSummary } from "@/api";
import { Button } from "@/components/ui/button";
import { Empty, EmptyDescription, EmptyHeader, EmptyMedia, EmptyTitle } from "@/components/ui/empty";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { formatInterval, formatRun, formatScore, plural } from "@/labels";
import { cn } from "@/lib/utils";
import { firstDirection, SORT_KEYS, sortRuns, type Direction, type SortKey } from "@/runTable";
import { scoreInterval } from "@/stats";

interface ColumnHeaderProps {
  column: SortKey;
  title: string;
  sort: SortKey;
  direction: Direction;
  onSort: (column: SortKey) => void;
  className?: string;
}

interface RunRowProps {
  run: RunSummary;
}

const ColumnHeader: React.FC<ColumnHeaderProps> = ({ column, title, sort, direction, onSort, className }) => {
  const active = column === sort;
  const Arrow = direction === "asc" ? ArrowUp : ArrowDown;
  return (
    <th
      scope="col"
      aria-sort={active ? (direction === "asc" ? "ascending" : "descending") : undefined}
      className={cn("px-1 py-2 font-normal", className)}
    >
      <Button
        variant="ghost"
        size="sm"
        className={cn("text-muted-foreground", active && "text-foreground")}
        onClick={() => onSort(column)}
      >
        {title}
        {active && <Arrow />}
      </Button>
    </th>
  );
};

const RunRow: React.FC<RunRowProps> = ({ run }) => {
  const navigate = useNavigate();
  const notes = [
    run.failed > 0 && `${run.failed} failed`,
    run.unmarked > 0 && `${run.unmarked} unmarked`,
  ].filter(Boolean);

  return (
    <tr className="cursor-pointer border-t hover:bg-accent" onClick={() => navigate(`/runs/${run.name}`)}>
      <td className="px-4 py-3 font-medium whitespace-nowrap">
        <Link to={`/runs/${run.name}`} onClick={event => event.stopPropagation()}>
          {formatRun(run.created)}
        </Link>
      </td>
      <td className="px-4 py-3">{run.model}</td>
      <td className={cn("px-4 py-3 font-mono text-xs", run.prompt === null && "text-muted-foreground")}>
        {run.prompt ?? "unknown"}
      </td>
      <td className="px-4 py-3 text-right tabular-nums">
        <Tooltip>
          <TooltipTrigger className="cursor-help" onClick={event => event.stopPropagation()}>
            {run.fixture_ids.length}
          </TooltipTrigger>
          <TooltipContent className="max-w-80">{run.fixture_ids.join(", ")}</TooltipContent>
        </Tooltip>
      </td>
      <td className="px-4 py-3 text-right whitespace-nowrap tabular-nums">
        <span className="font-medium">{formatScore(run.score)}</span>
        <span className="ml-2 text-xs text-muted-foreground">{formatInterval(scoreInterval(run))}</span>
      </td>
      <td className="px-4 py-3 text-right whitespace-nowrap tabular-nums">
        {run.answers}
        {notes.length > 0 && <span className="ml-2 text-xs text-muted-foreground">{notes.join(" · ")}</span>}
      </td>
    </tr>
  );
};

export const RunsScreen: React.FC = () => {
  const { data: runs } = useRuns();
  const [params, setParams] = useSearchParams();
  const sort = SORT_KEYS.find(key => key === params.get("sort")) ?? "created";
  const order = params.get("order");
  const direction: Direction = order === "asc" || order === "desc" ? order : firstDirection(sort);

  const onSort = (column: SortKey) => {
    const next = new URLSearchParams(params);
    next.set("sort", column);
    next.set("order", column === sort ? (direction === "asc" ? "desc" : "asc") : firstDirection(column));
    setParams(next, { replace: true });
  };

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

  const header = { sort, direction, onSort };

  return (
    <div className="h-full overflow-y-auto">
      <div className="mx-auto flex max-w-5xl flex-col gap-4 px-6 py-10">
        <div>
          <h1 className="text-lg font-semibold">Runs</h1>
          <p className="text-sm text-muted-foreground">
            Each score covers only its run's own fixtures, with a 95% interval. Sorting by score ranks runs by the low
            end of that interval, so a run with few answers does not top the list. Open a run to compare it with
            another on the fixtures both cover.
          </p>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left">
                <ColumnHeader column="created" title="Date" {...header} />
                <ColumnHeader column="model" title="Model" {...header} />
                <ColumnHeader column="prompt" title="Prompt" {...header} />
                <ColumnHeader column="fixtures" title="Fixtures" className="text-right" {...header} />
                <ColumnHeader column="score" title="Reasonable" className="text-right" {...header} />
                <ColumnHeader column="answers" title="Answers" className="text-right" {...header} />
              </tr>
            </thead>
            <tbody>
              {sortRuns(runs, sort, direction).map(run => (
                <RunRow key={run.name} run={run} />
              ))}
            </tbody>
          </table>
        </div>
        <p className="text-xs text-muted-foreground">{plural(runs.length, "run")}</p>
      </div>
    </div>
  );
};
