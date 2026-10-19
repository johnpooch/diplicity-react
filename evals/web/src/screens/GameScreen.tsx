import { useEffect, useMemo } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";
import { useGame } from "@/api";
import { CentreTimeline } from "@/components/CentreTimeline";
import { FeedbackPanel } from "@/components/FeedbackPanel";
import { GameAnswerPanel } from "@/components/GameAnswerPanel";
import { MapView } from "@/components/MapView";
import { PhaseStepper } from "@/components/PhaseStepper";
import { gameRenderState } from "@/gameBoard";
import { centreTimeline, firstPhaseOf, formatEnd, formatShare, phaseLabel } from "@/games";
import { plural } from "@/labels";

interface GameProps {
  name: string;
  seed: number;
}

const typing = (target: EventTarget | null): boolean =>
  target instanceof HTMLElement &&
  (target.isContentEditable || ["INPUT", "TEXTAREA", "SELECT"].includes(target.tagName));

const Game: React.FC<GameProps> = ({ name, seed }) => {
  const { data: game } = useGame(name, seed);
  const [params, setParams] = useSearchParams();
  const phase = game.phases.find(entry => entry.key === params.get("phase")) ?? game.phases[0];
  const state = useMemo(() => gameRenderState(phase), [phase]);
  const timeline = useMemo(() => centreTimeline(game.phases, game.final_centres), [game]);

  const select = (key: string) => {
    const next = new URLSearchParams(params);
    next.set("phase", key);
    setParams(next, { replace: true });
  };

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (typing(event.target) || event.altKey || event.ctrlKey || event.metaKey) return;
      const step = event.key === "ArrowLeft" ? -1 : event.key === "ArrowRight" ? 1 : 0;
      if (step === 0) return;
      const latest = new URLSearchParams(window.location.search);
      const at = Math.max(0, game.phases.findIndex(entry => entry.key === latest.get("phase")));
      const target = game.phases[at + step];
      if (!target) return;
      event.preventDefault();
      latest.set("phase", target.key);
      setParams(latest, { replace: true });
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [game, setParams]);

  return (
    <div className="flex h-full">
      <div className="flex min-w-0 flex-1 flex-col gap-4 p-6">
        <div className="flex flex-wrap items-baseline justify-between gap-x-6 gap-y-1">
          <div>
            <Link to={`/games/${name}`} className="text-sm text-muted-foreground hover:underline">
              Back to run
            </Link>
            <h1 className="text-lg font-semibold">
              {game.nation} · seed {game.seed} · {phaseLabel(phase.phase)}
            </h1>
          </div>
          <p className="text-sm text-muted-foreground">
            <span className="font-medium text-foreground">{formatShare(game.share)}</span> with{" "}
            {plural(game.centres, "centre")} · {formatEnd(game.end)}
          </p>
        </div>
        <PhaseStepper phases={game.phases} current={phase} notes={game.feedback} onSelect={select} />
        <div className="min-h-0 flex-1">
          <MapView state={state} />
        </div>
        <CentreTimeline
          points={timeline}
          nation={game.nation}
          currentYear={phase.phase.year}
          onSelect={year => {
            const target = firstPhaseOf(game.phases, year);
            if (target) select(target.key);
          }}
        />
      </div>
      <aside className="flex w-[24rem] shrink-0 flex-col gap-6 overflow-y-auto border-l p-6">
        <GameAnswerPanel phase={phase} nation={game.nation} />
      </aside>
      <aside className="flex w-[22rem] shrink-0 flex-col border-l p-6">
        <FeedbackPanel game={game} phase={phase} />
      </aside>
    </div>
  );
};

export const GameScreen: React.FC = () => {
  const { runName, seed } = useParams();
  return runName && seed ? <Game key={`${runName}|${seed}`} name={runName} seed={Number(seed)} /> : null;
};
