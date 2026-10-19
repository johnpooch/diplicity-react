import { Link, useNavigate } from "react-router-dom";
import { Inbox, TriangleAlert } from "lucide-react";
import { useGameRuns, type FeedbackOrphan, type GameRunSummary, type Reference } from "@/api";
import { Empty, EmptyDescription, EmptyHeader, EmptyMedia, EmptyTitle } from "@/components/ui/empty";
import { formatBand, formatCentres, formatShare, referenceBand } from "@/games";
import { formatRun, plural } from "@/labels";
import { cn } from "@/lib/utils";

interface GameRunRowProps {
  run: GameRunSummary;
  reference: Reference;
}

interface OrphansProps {
  orphans: FeedbackOrphan[];
}

const Orphans: React.FC<OrphansProps> = ({ orphans }) => (
  <div className="flex flex-col gap-2 rounded-md border border-destructive/40 bg-destructive/5 px-4 py-3 text-sm">
    <p className="flex items-center gap-2 font-medium text-destructive">
      <TriangleAlert className="size-4" />
      {plural(orphans.length, "feedback file")} without a game
    </p>
    <ul className="flex flex-col gap-1">
      {orphans.map(orphan => (
        <li key={orphan.path}>
          <span className="font-mono text-xs">{orphan.path}</span>
          <span className="text-muted-foreground"> · {orphan.problem}</span>
        </li>
      ))}
    </ul>
  </div>
);

const GameRunRow: React.FC<GameRunRowProps> = ({ run, reference }) => {
  const navigate = useNavigate();
  return (
    <tr className="cursor-pointer border-t hover:bg-accent" onClick={() => navigate(`/games/${run.name}`)}>
      <td className="px-4 py-3 font-medium whitespace-nowrap">
        <Link to={`/games/${run.name}`} onClick={event => event.stopPropagation()}>
          {formatRun(run.created)}
        </Link>
      </td>
      <td className="px-4 py-3">{run.model}</td>
      <td className={cn("px-4 py-3 font-mono text-xs", run.prompt === null && "text-muted-foreground")}>
        {run.prompt ?? "unknown"}
      </td>
      <td className="px-4 py-3">{run.nation}</td>
      <td className="px-4 py-3 text-right tabular-nums">{run.games}</td>
      <td className="px-4 py-3 text-right whitespace-nowrap tabular-nums">
        <span className="font-medium">{formatShare(run.share)}</span>
        <span className="ml-2 text-xs text-muted-foreground">{formatCentres(run.centres)} centres</span>
      </td>
      <td className="px-4 py-3 text-right text-xs whitespace-nowrap text-muted-foreground tabular-nums">
        {formatBand(referenceBand(reference))}
      </td>
      <td className="px-4 py-3 text-right tabular-nums">
        {run.with_feedback}/{run.games}
      </td>
    </tr>
  );
};

export const GamesScreen: React.FC = () => {
  const { data } = useGameRuns();

  if (data.runs.length === 0 && data.orphans.length === 0) {
    return (
      <Empty>
        <EmptyHeader>
          <EmptyMedia variant="icon">
            <Inbox />
          </EmptyMedia>
          <EmptyTitle>No games yet</EmptyTitle>
          <EmptyDescription>
            Play some with `python manage.py play_games --nation England` in evals/.
          </EmptyDescription>
        </EmptyHeader>
      </Empty>
    );
  }

  return (
    <div className="h-full overflow-y-auto">
      <div className="mx-auto flex max-w-6xl flex-col gap-4 px-6 py-10">
        <div>
          <h1 className="text-lg font-semibold">Games</h1>
          <p className="text-sm text-muted-foreground">
            The model plays one nation against six dumbbots to the end of 1905. A game scores its normalised sum of
            squares: its centres squared as a share of every nation's centres squared, or all of it on a solo. The
            dumbbot reference is dumbbot playing the same nation over 100 seeds, with a 95% interval for its mean.
          </p>
        </div>
        {data.orphans.length > 0 && <Orphans orphans={data.orphans} />}
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-muted-foreground">
                <th scope="col" className="px-4 py-2 font-normal">Date</th>
                <th scope="col" className="px-4 py-2 font-normal">Model</th>
                <th scope="col" className="px-4 py-2 font-normal">Prompt</th>
                <th scope="col" className="px-4 py-2 font-normal">Nation</th>
                <th scope="col" className="px-4 py-2 text-right font-normal">Games</th>
                <th scope="col" className="px-4 py-2 text-right font-normal">Mean share</th>
                <th scope="col" className="px-4 py-2 text-right font-normal">Dumbbot reference</th>
                <th scope="col" className="px-4 py-2 text-right font-normal">Feedback</th>
              </tr>
            </thead>
            <tbody>
              {data.runs.map(run => (
                <GameRunRow key={run.name} run={run} reference={data.references[run.nation] ?? null} />
              ))}
            </tbody>
          </table>
        </div>
        <p className="text-xs text-muted-foreground">{plural(data.runs.length, "game run")}</p>
      </div>
    </div>
  );
};
