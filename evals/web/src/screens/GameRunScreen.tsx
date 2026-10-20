import { Link, useNavigate, useParams } from "react-router-dom";
import { useGameRun, type GameRunGame } from "@/api";
import { PromptDiff } from "@/components/PromptDiff";
import { formatBand, formatCentres, formatEnd, formatShare, referenceBand } from "@/games";
import { formatRun, plural } from "@/labels";
import { cn } from "@/lib/utils";

interface GameRunProps {
  name: string;
}

interface GameRowProps {
  name: string;
  game: GameRunGame;
}

const GameRow: React.FC<GameRowProps> = ({ name, game }) => {
  const navigate = useNavigate();
  const to = `/games/${name}/${game.seed}`;
  return (
    <tr className="cursor-pointer border-t hover:bg-accent" onClick={() => navigate(to)}>
      <td className="px-4 py-3 font-medium tabular-nums">
        <Link to={to} onClick={event => event.stopPropagation()}>
          Seed {game.seed}
        </Link>
      </td>
      <td className="px-4 py-3 text-right whitespace-nowrap tabular-nums">
        <span className="font-medium">{formatShare(game.share)}</span>
        <span className="ml-2 text-xs text-muted-foreground">{plural(game.centres, "centre")}</span>
      </td>
      <td className="px-4 py-3 text-right whitespace-nowrap text-muted-foreground tabular-nums">
        {formatShare(game.paired_share)}
        <span className="ml-2 text-xs">{plural(game.paired_centres, "centre")}</span>
      </td>
      <td className="px-4 py-3">{formatEnd(game.end)}</td>
      <td className={cn("px-4 py-3 text-right tabular-nums", game.failed === 0 && "text-muted-foreground")}>
        {game.failed}
      </td>
      <td className="px-4 py-3 text-center">
        {game.feedback ? (
          <span className="inline-block size-2 rounded-full bg-foreground" aria-label="Has feedback" />
        ) : (
          <span className="sr-only">No feedback</span>
        )}
      </td>
    </tr>
  );
};

const GameRun: React.FC<GameRunProps> = ({ name }) => {
  const { data: run } = useGameRun(name);
  const band = referenceBand(run.reference);

  return (
    <div className="h-full overflow-y-auto">
      <div className="mx-auto flex max-w-4xl flex-col gap-12 px-6 py-10">
        <header className="flex flex-col gap-6">
          <div>
            <Link to="/games" className="text-sm text-muted-foreground hover:underline">
              Games
            </Link>
            <h1 className="text-lg font-semibold">
              {run.nation} · {formatRun(run.created)}
            </h1>
            <p className="text-sm text-muted-foreground">
              {run.model} · <span className="font-mono">{run.prompt ?? "unknown prompt"}</span> ·{" "}
              <a href="#opening-prompt" className="hover:underline">
                opening prompt
              </a>
            </p>
          </div>
          <div className="flex flex-wrap items-end gap-x-12 gap-y-4">
            <div>
              <p className="text-5xl font-semibold">
                {formatShare(run.share)}
                <span className="ml-2 text-xl font-normal text-muted-foreground">mean share</span>
              </p>
              <p className="mt-1 text-sm text-muted-foreground">
                {formatCentres(run.centres)} centres on average over {plural(run.games.length, "game")}
              </p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">
                Dumbbot as {run.nation}
                {band && `, ${plural(band.games, "seed")}`}
              </p>
              <p className="font-medium tabular-nums">{formatBand(band)}</p>
            </div>
          </div>
        </header>
        <section className="flex flex-col gap-2">
          <h2 className="font-semibold">Games</h2>
          <p className="text-sm text-muted-foreground">
            Each seed is also played with dumbbot in {run.nation}'s seat against the same opponents.
          </p>
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-muted-foreground">
                <th scope="col" className="px-4 py-2 font-normal">Game</th>
                <th scope="col" className="px-4 py-2 text-right font-normal">Model</th>
                <th scope="col" className="px-4 py-2 text-right font-normal">Dumbbot, same seed</th>
                <th scope="col" className="px-4 py-2 font-normal">Ended</th>
                <th scope="col" className="px-4 py-2 text-right font-normal">Failed phases</th>
                <th scope="col" className="px-4 py-2 text-center font-normal">Feedback</th>
              </tr>
            </thead>
            <tbody>
              {run.games.map(game => (
                <GameRow key={game.seed} name={name} game={game} />
              ))}
            </tbody>
          </table>
        </section>
        <section id="opening-prompt" className="flex scroll-mt-6 flex-col gap-4">
          <h2 className="font-semibold">
            Opening prompt
            <span className="ml-2 font-mono text-sm font-normal text-muted-foreground">{run.prompt ?? "unknown"}</span>
          </h2>
          <p className="text-sm text-muted-foreground">
            What {run.nation} is sent on the Spring 1901 board. Every phase sends the same prompt rendered for its own
            board.
          </p>
          <PromptDiff title="System prompt" before={null} after={run.opening?.system ?? ""} />
          <PromptDiff title="User prompt" before={null} after={run.opening?.user ?? ""} />
        </section>
      </div>
    </div>
  );
};

export const GameRunScreen: React.FC = () => {
  const { runName } = useParams();
  return runName ? <GameRun key={runName} name={runName} /> : null;
};
